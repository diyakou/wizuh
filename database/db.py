from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL
import logging
from sqlalchemy.orm import declarative_base
Base = declarative_base()

logger = logging.getLogger(__name__)

# Create database engine
try:
    engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = scoped_session(SessionLocal)
except SQLAlchemyError as e:
    logger.error(f"Database connection error: {e}")
    raise

def get_db():
    """Get database session."""
    db = session()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise 