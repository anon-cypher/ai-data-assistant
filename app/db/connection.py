from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import DBConfig

# Expect `DATABASE_URL` to be present in environment. `.env` is loaded in `app.main`.
engine = create_engine(DBConfig.DATABASE_URL_ENV)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
