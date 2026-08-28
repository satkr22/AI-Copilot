from fastapi import FastAPI
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.user import router as user_router
from app.api.routes.project import router as project_router
from app.api.routes.repository import router as repository_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(project_router)
app.include_router(repository_router)


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