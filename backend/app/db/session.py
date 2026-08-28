from app.core.config import settings
from sqlalchemy import create_engine

database_url = settings.DATABASE_URL
engine = create_engine