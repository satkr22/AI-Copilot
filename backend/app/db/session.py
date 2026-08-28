from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url = settings.DATABASE_URL

engine = create_engine(
    url=database_url,
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# fucntion to create one seesion
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()