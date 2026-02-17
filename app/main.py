from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

from app.utils.config import LLMConfig, DBConfig
from app.routes.chats import router as chat_router

def _validate_env():
    missing = []
    if not LLMConfig.OPENAI_API_KEY_ENV:
        missing.append(LLMConfig.OPENAI_API_KEY_ENV)
    if not DBConfig.DATABASE_URL_ENV:
        missing.append(DBConfig.DATABASE_URL_ENV)

    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


_validate_env()


app = FastAPI(title="AI Data Assistant")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)


@app.get("/v1")
def root():
    return {"status": "running"}
