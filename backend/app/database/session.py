from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config.config import settings

# Create standard SQLAlchemy engine
# pool_pre_ping checks the connection before executing queries to prevent stale connection errors
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Setup Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for models
Base = declarative_base()

# Database Dependency to inject session into endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
