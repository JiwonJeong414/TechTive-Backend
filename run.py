"""
run.py

Entry point for creating and running the Flask application.
"""

from app import create_app

# Create an instance of the Flask application using the factory function
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
