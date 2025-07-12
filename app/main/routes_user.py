from flask import Blueprint, request, jsonify
from app.utils.aws_utils import allowed_file, generate_unique_filename, resize_image, upload_to_s3, delete_from_s3
from app.extensions import db 
from app.models.user import User
from app.auth.firebase_auth import firebase_auth_required
from botocore.exceptions import ClientError

user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/pfp/', methods=['POST'])
@firebase_auth_required
def upload_profile_picture():
    # Check if file is present
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed'}), 400
    
    try:
        user_id = request.user.id
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user already has a profile picture
        if user.profile_picture_url and user.profile_picture_filename:
            return jsonify({
                'error': 'Profile picture already exists. Use PUT /api/pfp/ to update it.',
                'existing_url': user.profile_picture_url
            }), 409
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Resize image
        resized_image = resize_image(file)
        
        # Upload to S3
        s3_url = upload_to_s3(resized_image, filename)
        
        if s3_url:
            user.profile_picture_url = s3_url
            user.profile_picture_filename = filename
            db.session.commit()
            return jsonify({
                'message': 'Profile picture uploaded successfully',
                'url': s3_url,
                'filename': filename
            }), 200
        else:
            return jsonify({'error': 'Failed to upload image'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500 

@user_bp.route('/pfp/', methods=['PUT'])
@firebase_auth_required
def update_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['profile_picture']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    
    try:
        user_id = request.user.id
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current profile picture filename from database
        current_filename = user.profile_picture_filename
        
        # Delete old profile picture from S3 if it exists
        if current_filename:
            delete_from_s3(current_filename)
        
        # Upload new profile picture
        filename = generate_unique_filename(file.filename)
        resized_image = resize_image(file)
        s3_url = upload_to_s3(resized_image, filename)
        
        if s3_url:
            # Update database with new profile picture
            user.profile_picture_url = s3_url
            user.profile_picture_filename = filename
            db.session.commit()
            return jsonify({
                'message': 'Profile picture updated successfully',
                'url': s3_url,
                'filename': filename
            }), 200
        else:
            return jsonify({'error': 'Failed to update image'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500 

@user_bp.route('/pfp/', methods=['DELETE'])
@firebase_auth_required
def delete_profile_picture():
    try:
        user_id = request.user.id
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current profile picture filename from database
        current_filename = user.profile_picture_filename
        
        if current_filename:
            # Delete from S3
            if delete_from_s3(current_filename):
                # Remove from database
                user.profile_picture_url = None
                user.profile_picture_filename = None
                db.session.commit()
                return jsonify({'message': 'Profile picture deleted successfully'}), 200
            else:
                return jsonify({'error': 'Failed to delete image from storage'}), 500
        else:
            return jsonify({'error': 'No profile picture found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500 

@user_bp.route('/pfp/', methods=['GET'])
@firebase_auth_required
def get_profile_picture():
    try:
        user_id = request.user.id
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        profile_url = user.profile_picture_url
        
        if profile_url:
            return jsonify({'profile_picture_url': profile_url}), 200
        else:
            return jsonify({'message': 'No profile picture found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve profile picture: {str(e)}'}), 500 