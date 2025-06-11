from flask import Flask
from app.extensions import db, ma, migrate
from app.config import config
from app.main import blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    return app
