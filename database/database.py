import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "netsage.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

db = SQLAlchemy()

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False} # Needed for SQLite in Flask
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db(app):
    """Initializes the database with the Flask app instance and creates tables."""
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
        
    db.init_app(app)
    with app.app_context():
        from database.models import DiagnosticRecord, HumanReviewLog, ReviewLog
        
        db.create_all()

def get_db():
    """Dependency to get the database session."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()