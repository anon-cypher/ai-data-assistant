import os
from langchain_openai import ChatOpenAI
from langsmith import traceable
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver


MODEL_INSIGHT = "gpt-4o-mini"  # cheap, good for summarization
config = {"configurable": {"thread_id": "chat-1"}}
memory = MemorySaver()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

@tool
def describe_dataset(columns: list, rows: list) -> str:
    """Summarizes dataset structure for analysis."""
    return f"Columns: {columns}\nSample Rows: {rows[:5]}"

tools = [describe_dataset]

@traceable(name="insight_generation")
def generate_insight(question, columns, rows):
    # Limit rows to avoid large prompts
    sample_rows = rows[:10]

    prompt = f"""
User asked: {question}

You have access to dataset tools.
Analyze the result and provide key insights.
Focus on trends, outliers, and notable comparisons.
"""

    deep_agent = create_deep_agent(
    model=llm,
    tools=tools,
    system_prompt=prompt,
    checkpointer=memory
    )

    res = deep_agent.invoke({"messages": [{"role": "user", "content": f"{[columns, rows]}"}]}, config=config)

    print("Result : ", res["messages"][-1].content)

    return res["messages"][-1].content

