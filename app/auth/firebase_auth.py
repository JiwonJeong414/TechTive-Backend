from functools import wraps
from flask import request, jsonify, current_app
import firebase_admin
from firebase_admin import credentials, auth
from app.models.user import User
from app.extensions import db
import os

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
    except ValueError:
        # Get the path from environment variable or use a default path
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'config/serviceAccountKey.json')
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account key file not found at {service_account_path}. "
                "Please set FIREBASE_SERVICE_ACCOUNT_PATH environment variable or place the file at config/serviceAccountKey.json"
            )
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

def get_or_create_user(firebase_uid):
    """Get existing user or create new one from Firebase UID"""
    user = User.query.filter_by(firebase_uid=firebase_uid).first()
    if not user:
        user = User(firebase_uid=firebase_uid)
        db.session.add(user)
        db.session.commit()
    return user

def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401

        token = auth_header.split('Bearer ')[1]
        try:
            # Verify the Firebase token
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token['uid']
            
            # Get or create user in our database
            user = get_or_create_user(firebase_uid)
            
            # Add user to request context
            request.user = user
            
            return f(*args, **kwargs)
        except Exception as e:
            print("Firebase token verification error:", e)
            return jsonify({'error': 'Invalid token'}), 401

    return decorated_function 