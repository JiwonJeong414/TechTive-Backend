from functools import wraps
from flask import request, jsonify, current_app
import firebase_admin
from firebase_admin import credentials, auth
from app.models.user import User
from app.extensions import db
import os
import logging
import requests
from requests.exceptions import RequestException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized")
    except ValueError:
        # Get the path from environment variable or use a default path
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'config/serviceAccountKey.json')
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account key file not found at {service_account_path}. "
                "Please set FIREBASE_SERVICE_ACCOUNT_PATH environment variable or place the file at config/serviceAccountKey.json"
            )
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise

def check_network_connectivity():
    """Check if we can reach Firebase's servers"""
    try:
        # Test connection to Firebase Auth servers
        response = requests.get('https://www.googleapis.com/identitytoolkit/v3/relyingparty/publicKeys', timeout=10)
        if response.status_code == 200:
            logger.info("Network connectivity to Firebase servers: OK")
            return True
        else:
            logger.warning(f"Firebase servers responded with status code: {response.status_code}")
            return False
    except RequestException as e:
        logger.error(f"Network connectivity test failed: {e}")
        return False

def get_or_create_user(firebase_uid):
    """Get existing user or create new one from Firebase UID"""
    user = User.query.filter_by(firebase_uid=firebase_uid).first()
    if not user:
        user = User(firebase_uid=firebase_uid)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user with Firebase UID: {firebase_uid}")
    else:
        logger.info(f"Found existing user with Firebase UID: {firebase_uid}")
    return user

def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("No Authorization header or invalid format")
            return jsonify({'error': 'No token provided'}), 401

        token = auth_header.split('Bearer ')[1]
        
        # Check network connectivity first
        if not check_network_connectivity():
            logger.error("Cannot reach Firebase servers - network connectivity issue")
            return jsonify({
                'error': 'Authentication service unavailable',
                'details': 'Cannot connect to Firebase authentication servers. Please check your network connection.'
            }), 503

        try:
            # Verify the Firebase token
            logger.info("Attempting to verify Firebase token")
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token['uid']
            logger.info(f"Token verified successfully for UID: {firebase_uid}")
            
            # Get or create user in our database
            user = get_or_create_user(firebase_uid)
            
            # Add user to request context
            request.user = user
            
            return f(*args, **kwargs)
        except auth.ExpiredIdTokenError:
            logger.warning("Firebase token has expired")
            return jsonify({'error': 'Token expired'}), 401
        except auth.RevokedIdTokenError:
            logger.warning("Firebase token has been revoked")
            return jsonify({'error': 'Token revoked'}), 401
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase token provided")
            return jsonify({'error': 'Invalid token'}), 401
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during token verification: {e}")
            return jsonify({
                'error': 'Authentication service unavailable',
                'details': 'Cannot connect to Firebase authentication servers. Please try again later.'
            }), 503
        except Exception as e:
            logger.error(f"Unexpected error during Firebase token verification: {e}")
            return jsonify({
                'error': 'Authentication failed',
                'details': 'An unexpected error occurred during authentication.'
            }), 500

    return decorated_function 