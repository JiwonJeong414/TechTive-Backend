import os
from dotenv import load_dotenv

load_dotenv()

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

    # OPEN AI API
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

config = Config()