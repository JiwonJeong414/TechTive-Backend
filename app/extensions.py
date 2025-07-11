from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from celery import Celery, Task
import boto3
from botocore.exceptions import ClientError

# Initialize Celery with proper configuration
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


# Initialize S3 client with config values (to be called after app is created)
s3_client = None
def init_s3_client(app: Flask):
    global s3_client
    from app.config import config
    
    print(f"DEBUG: Initializing S3 client...")
    print(f"DEBUG: AWS_ACCESS_KEY_ID: {'SET' if config.AWS_ACCESS_KEY_ID else 'NOT SET'}")
    print(f"DEBUG: AWS_SECRET_ACCESS_KEY: {'SET' if config.AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
    print(f"DEBUG: AWS_REGION: {config.AWS_REGION}")
    print(f"DEBUG: S3_BUCKET_NAME: {config.S3_BUCKET_NAME}")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        print(f"DEBUG: S3 client initialized successfully")
        app.extensions["s3_client"] = s3_client
    except Exception as e:
        print(f"ERROR: Failed to initialize S3 client: {e}")
        s3_client = None


db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()