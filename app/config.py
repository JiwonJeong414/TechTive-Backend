import os
from celery.schedules import crontab

# Get the base directory of the current file
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Firebase Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")

    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

    # Hugging Face API
    HUGGING_FACE_API_TOKEN = os.environ.get("HUGGING_FACE_API_TOKEN")
    HUGGING_FACE_MODEL_URL = os.environ.get("HUGGING_FACE_MODEL_URL", "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base")


config = Config()