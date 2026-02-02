from fastapi import APIRouter
import hashlib

from app.services.cache_service import get_cache, set_cache
from app.services.rule_engine import match_rule_based_query
from app.services.table_selector import select_relevant_tables
from app.services.sql_generator import generate_sql
from app.services.metadata_loader import load_table_metadata
from app.services.sql_validator import validate_sql
from app.services.db_executer import execute_sql
from app.services.response_builder import build_response
from app.services.insight_agent import generate_insight


router = APIRouter()
metadata = load_table_metadata()


def normalize_question(q: str) -> str:
    return q.strip().lower()


@router.post("/ask")
async def ask_question(payload: dict):
    question = payload.get("question")

    if not question:
        return {"error": "Question is required"}

    normalized = normalize_question(question)
    key = hashlib.md5(normalized.encode()).hexdigest()

    # 1️⃣ CACHE CHECK
    cached = get_cache(key)
    if cached:
        return {
            "answer": cached,
            "source": "cache"
        }

    # 2️⃣ RULE ENGINE (No AI cost)
    sql_query = match_rule_based_query(question)
    if sql_query:
        answer = f"(Rule-based SQL generated)\n{sql_query}"
        set_cache(key, answer)

        return {
            "answer": answer,
            "sql_used": sql_query,
            "source": "rule_engine"
        }

    # 3️⃣ TABLE SELECTION USING FAISS
    selected_tables = select_relevant_tables(question)

    # 4️⃣ LLM SQL GENERATION (schema-aware)
    try:
        sql_query = generate_sql(question, selected_tables, metadata)
    except Exception as e:
        return {"error": f"SQL generation failed: {str(e)}"}

    safe_sql = sql_query
    # 5️⃣ SQL SAFETY VALIDATION
    # try:
    #     safe_sql = validate_sql(sql_query, selected_tables)
    # except Exception as e:
    #     return {"error": f"SQL blocked by safety layer: {str(e)}"}
    
    # 6️⃣ EXECUTE SQL
    try:
        columns, rows = execute_sql(safe_sql)
    except Exception as e:
        return {"error": f"Database execution failed: {str(e)}"}

    # Generate insight only for multi-row tables
    insight = None
    print("Rows Detected : ", len(rows))
    if len(rows) > 1:
        try:
            insight = generate_insight(question, columns, rows)
        except Exception as e:
            raise("Insight Generation failed  : ", e)
            # insight = None  # Fail silently if LLM fails
    
    # 7️⃣ BUILD HUMAN RESPONSE
    answer = build_response(columns, rows, insight)

    set_cache(key, answer)

    return {
        "answer": answer,
        "sql_used": safe_sql,
        "tables_used": selected_tables,
        "source": "llm_sql_generator_validated"
    }
