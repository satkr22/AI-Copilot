from fastapi import FastAPI
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.VITE_FRONTEND_API_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }
    
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-copilot-backend"
    }