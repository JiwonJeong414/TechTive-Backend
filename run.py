# app.py
from flask import Flask
from extensions import db, ma
import config
from main import blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register all blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
