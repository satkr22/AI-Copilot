from fastapi import FastAPI
from app.core.config import settings

app = FastAPI()

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