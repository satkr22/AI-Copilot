from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FastAPI_App"
    ENVIRONMENT: str = "development"
    
    # API keys
    OPENAI_API_KEY: str
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    
    # Qdrant
    QDRANT_URL: str 
    QDRANT__SERVICE__API_KEY: str
    
    # frontend
    VITE_FRONTEND_API_URL: str
    
    # debug settings
    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    # docker will inject env variables to container's enviornment and pydantic will read from the container's environment too
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


# Create a global settings instance
settings = Settings() #type: ignore