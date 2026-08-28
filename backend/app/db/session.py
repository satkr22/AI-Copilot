from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url = settings.DATABASE_URL

engine = create_engine(
    url=database_url,
    echo=True
)

session = sessionmaker(
    bind=engine,
    autoflush=False
)
