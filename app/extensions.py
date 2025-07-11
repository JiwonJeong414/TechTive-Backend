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
    
    # Check if all required config values are present
    if not config.AWS_ACCESS_KEY_ID:
        print("ERROR: AWS_ACCESS_KEY_ID environment variable is not set")
        return False
        
    if not config.AWS_SECRET_ACCESS_KEY:
        print("ERROR: AWS_SECRET_ACCESS_KEY environment variable is not set")
        return False
        
    if not config.S3_BUCKET_NAME:
        print("ERROR: S3_BUCKET_NAME environment variable is not set")
        return False
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_REGION
        )
        
        # Test the connection by listing buckets
        try:
            s3_client.head_bucket(Bucket=config.S3_BUCKET_NAME)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"ERROR: S3 bucket '{config.S3_BUCKET_NAME}' does not exist")
            elif error_code == '403':
                print(f"ERROR: Access denied to S3 bucket '{config.S3_BUCKET_NAME}'. Check your AWS credentials and bucket permissions.")
            else:
                print(f"ERROR: Failed to access S3 bucket: {error_code} - {e.response['Error']['Message']}")
            return False
        
        app.extensions["s3_client"] = s3_client
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to initialize S3 client: {e}")
        s3_client = None
        return False

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()