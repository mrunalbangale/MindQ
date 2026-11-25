from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import documents, quiz, youtube
from app.services.llm import get_gemini_api_key, get_gemini_model, is_llm_configured

app = FastAPI(
    title="MindQ API",
    description="MindQ — PDF & YouTube Quiz Generator",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(youtube.router)
app.include_router(quiz.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_configured": is_llm_configured(),
        "gemini_key_set": bool(get_gemini_api_key()),
        "model": get_gemini_model(),
    }
