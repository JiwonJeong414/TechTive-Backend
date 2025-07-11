import uuid
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from app.config import config

def get_s3_client():
    """Get the S3 client from extensions, with fallback initialization"""
    from app.extensions import s3_client
    
    if s3_client is None:
        print("WARNING: S3 client is None, attempting to initialize...")
        import boto3
        
        # Check if all required config values are present
        if not all([config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY, config.S3_BUCKET_NAME]):
            print("ERROR: Missing required AWS configuration")
            return None
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            return s3_client
        except Exception as e:
            print(f"ERROR: Failed to initialize S3 client as fallback: {e}")
            return None
    
    return s3_client

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
        # Get S3 client with fallback
        client = get_s3_client()
        if client is None:
            print("ERROR: S3 client is not available")
            return None
        
        # Debug: Check if config values are set
        if not config.S3_BUCKET_NAME:
            print(f"ERROR: S3_BUCKET_NAME is not set. Current value: {config.S3_BUCKET_NAME}")
            return None
        
        if not config.AWS_REGION:
            print(f"ERROR: AWS_REGION is not set. Current value: {config.AWS_REGION}")
            return None
        
        # Try upload without ACL first (for buckets with ACLs disabled)
        try:
            client.upload_fileobj(
                file_obj,
                config.S3_BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': content_type
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessControlListNotSupported':
                print("INFO: Bucket has ACLs disabled, uploading without ACL")
                client.upload_fileobj(
                    file_obj,
                    config.S3_BUCKET_NAME,
                    filename,
                    ExtraArgs={
                        'ContentType': content_type
                    }
                )
            else:
                raise  # Re-raise if it's a different error
        
        s3_url = f"https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{filename}"
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
        # Get S3 client with fallback
        client = get_s3_client()
        if client is None:
            print("ERROR: S3 client is not available")
            return False
        
        # Debug: Check if config values are set
        if not config.S3_BUCKET_NAME:
            print(f"ERROR: S3_BUCKET_NAME is not set. Current value: {config.S3_BUCKET_NAME}")
            return False
        
        client.delete_object(Bucket=config.S3_BUCKET_NAME, Key=filename)
        
        return True
        
    except ClientError as e:
        print(f"ERROR deleting from S3: {e}")
        print(f"Error Code: {e.response['Error']['Code']}")
        print(f"Error Message: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"UNEXPECTED ERROR deleting from S3: {type(e).__name__}: {e}")
        return False
