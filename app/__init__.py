from flask import Flask
from app.extensions import db, ma, migrate, celery_init_app, init_s3_client
from app.config import config
from app.main import blueprints
from app.auth.firebase_auth import init_firebase

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.config["CELERY"] = {
        "broker_url": config.CELERY_BROKER_URL,
        "result_backend": config.CELERY_RESULT_BACKEND
    }
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Celery
    celery_init_app(app)
    
    # Initialize S3
    init_s3_client(app)
    
    # Initialize Firebase
    init_firebase()
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    return app
