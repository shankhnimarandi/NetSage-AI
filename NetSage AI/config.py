import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for NetSage AI Flask application."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "netsage-ai-secure-secret-key")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    CASES_FILE = os.path.join(BASE_DIR, "cases.csv")
    DIAGNOSE_FILE = os.path.join(BASE_DIR, "diagnose.csv")
    REVIEW_FILE = os.path.join(BASE_DIR, "human_review_log.csv")
    PROMPT_FILE = os.path.join(BASE_DIR, "diagnose_prompt.txt")
    VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
    FAISS_INDEX_PATH = os.path.join(VECTORSTORE_DIR, "index.faiss")
    FAISS_PKL_PATH = os.path.join(VECTORSTORE_DIR, "index.pkl")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}