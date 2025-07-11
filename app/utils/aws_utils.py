import uuid
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from app.config import config
from app.extensions import s3_client

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename to avoid conflicts"""
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def resize_image(image_file, max_size=(800, 800)):
    """Resize image to optimize storage"""
    image = Image.open(image_file)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary (for JPEG)
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')
    
    # Save to BytesIO object
    output = BytesIO()
    image.save(output, format='JPEG', quality=85)
    output.seek(0)
    return output

def upload_to_s3(file_obj, filename, content_type='image/jpeg'):
    """Upload file to S3 bucket"""
    try:
        # Debug: Check if s3_client is initialized
        if s3_client is None:
            print("ERROR: s3_client is None - S3 client not initialized")
            print("Make sure init_s3_client(app) was called in your app factory")
            return None
        
        # Debug: Check if config values are set
        if not config.S3_BUCKET_NAME:
            print(f"ERROR: S3_BUCKET_NAME is not set. Current value: {config.S3_BUCKET_NAME}")
            return None
        
        if not config.AWS_REGION:
            print(f"ERROR: AWS_REGION is not set. Current value: {config.AWS_REGION}")
            return None
        
        print(f"DEBUG: Attempting to upload {filename} to bucket {config.S3_BUCKET_NAME} in region {config.AWS_REGION}")
        
        s3_client.upload_fileobj(
            file_obj,
            config.S3_BUCKET_NAME,
            filename,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'  # Make file publicly accessible
            }
        )
        
        s3_url = f"https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{filename}"
        print(f"DEBUG: Successfully uploaded to {s3_url}")
        return s3_url
        
    except ClientError as e:
        print(f"ERROR uploading to S3: {e}")
        print(f"Error Code: {e.response['Error']['Code']}")
        print(f"Error Message: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"UNEXPECTED ERROR uploading to S3: {type(e).__name__}: {e}")
        return None


def delete_from_s3(filename):
    """Delete file from S3 bucket"""
    try:
        # Debug: Check if s3_client is initialized
        if s3_client is None:
            print("ERROR: s3_client is None - S3 client not initialized")
            return False
        
        # Debug: Check if config values are set
        if not config.S3_BUCKET_NAME:
            print(f"ERROR: S3_BUCKET_NAME is not set. Current value: {config.S3_BUCKET_NAME}")
            return False
        
        print(f"DEBUG: Attempting to delete {filename} from bucket {config.S3_BUCKET_NAME}")
        
        s3_client.delete_object(Bucket=config.S3_BUCKET_NAME, Key=filename)
        
        print(f"DEBUG: Successfully deleted {filename}")
        return True
        
    except ClientError as e:
        print(f"ERROR deleting from S3: {e}")
        print(f"Error Code: {e.response['Error']['Code']}")
        print(f"Error Message: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR deleting from S3: {type(e).__name__}: {e}")
        return False