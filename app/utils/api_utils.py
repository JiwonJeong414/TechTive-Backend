import requests
from app.config import config

def call_hf_emotion_api(content):
    """
    Call Hugging Face Inference API for emotion analysis
    
    Args:
        content (str): Text content to analyze
        
    Returns:
        list: List of emotion predictions with labels and scores
        
    Raises:
        Exception: If API call fails
    """
    # Get API token from config
    api_token = config.HUGGING_FACE_API_TOKEN
    if not api_token:
        raise Exception("HUGGING_FACE_API_TOKEN not configured")
    
    # Set up the API request
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    # Use the model URL from config
    api_url = config.HUGGING_FACE_MODEL_URL

    payload = {
        "inputs": content 
    }
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}")
        
        emotion_data = response.json()
        
        # Handle the case where the model is loading
        if isinstance(emotion_data, dict) and "error" in emotion_data:
            if "loading" in emotion_data["error"].lower():
                print("Model is loading, will retry...")
                raise Exception("Model is loading, retry needed")
            else:
                raise Exception(f"API error: {emotion_data['error']}")
        
        emotions = None
        
        if isinstance(emotion_data, list):
            if len(emotion_data) > 0:
                emotions = emotion_data[0]  # Nested format
        
        # Validate we have the emotions in the expected format
        if not emotions or not isinstance(emotions, list):
            raise Exception(f"Could not extract emotion data from response")
        
        # Validate emotion objects have required fields
        for emotion in emotions:
            if not isinstance(emotion, dict) or "label" not in emotion or "score" not in emotion:
                raise Exception(f"Invalid emotion object format")
        
        return emotions
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {e}")
    except Exception as e:
        raise 