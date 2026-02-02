from fastapi import FastAPI
from app.routes.chats import router as chat_router

app = FastAPI(title="AI Data Assistant")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)




@app.get("/")
def root():
    return {"status": "running"}
