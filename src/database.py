from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

def get_database_url() -> str:
    try:
        from src.config_loader import load_config
        config = load_config()
        return config.database.url
    except Exception:
        return "sqlite:///ratio_scanner.db"

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
