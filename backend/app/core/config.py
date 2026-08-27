from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FastAPI_App"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL_v1: str
    
    # API keys
    OPENAI_API_KEY: str
    # Qdrant
    QDRANT_URL: str 
    
    # debug settings
    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    # this is not needed for the docker implementation as docker will inject env variables to containers' enviornment and pydantic will read from the environment too
    
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     case_sensitive = True

# Create a global settings instance
settings = Settings() #type: ignore