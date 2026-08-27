from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FastAPI_App"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL_v1: str = "postgresql://user:password@localhost:5432/dbname"
    
    # API keys
    OPENAI_API_KEY: str = ""
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # debug settings
    DEBUG: bool = ENVIRONMENT == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create a global settings instance
settings = Settings()