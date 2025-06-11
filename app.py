# app.py
from flask import Flask, jsonify
from extensions import db, ma
import config
from user import User

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
ma.init_app(app)

@app.route("/")
def home():
    return jsonify(message="Hello from Flask!")

if __name__ == "__main__":
    app.run(debug=True)
