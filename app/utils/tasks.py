import gc
import os
import requests
from time import sleep
from celery import shared_task
from app.models.note import Note
from app.extensions import db

# Supported emotions to prevent API changes from breaking the model
SUPPORTED_EMOTIONS = {
    "anger",
    "disgust", 
    "fear",
    "joy",
    "neutral",
    "sadness",
    "surprise",
}

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
    # Get API token from environment
    api_token = os.environ.get('HUGGING_FACE_API_TOKEN')
    if not api_token:
        raise Exception("HUGGING_FACE_API_TOKEN environment variable not set")
    
    # Set up the API request
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    # Use the Hugging Face Inference API URL
    api_url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
    
    payload = {
        "inputs": content[:500]  # Limit content length
    }
    
    try:
        print("Sending request to Hugging Face Inference API...")
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"API returned status {response.status_code}: {response.text}")
            raise Exception(f"API request failed with status {response.status_code}")
        
        emotion_data = response.json()
        
        # Handle the case where the model is loading
        if isinstance(emotion_data, dict) and "error" in emotion_data:
            if "loading" in emotion_data["error"].lower():
                print("Model is loading, will retry...")
                raise Exception("Model is loading, retry needed")
            else:
                raise Exception(f"API error: {emotion_data['error']}")
        
        # Validate response format
        if not isinstance(emotion_data, list) or len(emotion_data) == 0:
            raise Exception("Invalid response format from API")
        
        # Get the first result (emotion classifications)
        emotions = emotion_data[0]
        if not isinstance(emotions, list) or len(emotions) < 7:
            raise Exception("Invalid emotion data in response")
        
        print(f"Successfully received emotion data: {len(emotions)} emotions")
        return emotions
        
    except requests.exceptions.RequestException as e:
        print(f"Network error during API call: {e}")
        raise Exception(f"Network error: {e}")
    except Exception as e:
        print(f"Error calling Hugging Face API: {e}")
        raise

def analyze_with_keywords_fallback(content):
    """
    Fallback keyword-based emotion analysis
    """
    content_lower = content.lower()
    
    emotion_keywords = {
        "joy": ["happy", "joy", "joyful", "excited", "great", "awesome", "love", "wonderful", "amazing"],
        "sadness": ["sad", "depressed", "down", "upset", "cry", "disappointed", "hurt", "sorrow"],
        "anger": ["angry", "mad", "furious", "hate", "annoyed", "frustrated", "irritated", "rage"],
        "fear": ["scared", "afraid", "worried", "anxious", "nervous", "terrified", "panic", "frightened"],
        "disgust": ["disgusted", "gross", "sick", "revolted", "nasty", "awful", "terrible", "horrible"],
        "surprise": ["surprised", "shocked", "amazed", "unexpected", "wow", "incredible", "astonished"]
    }
    
    emotion_scores = {}
    word_count = len(content_lower.split())
    
    for emotion, keywords in emotion_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        score = min(matches / max(1, word_count * 0.1), 1.0)
        emotion_scores[emotion] = score
    
    # Add neutral score
    total_emotion = sum(emotion_scores.values())
    emotion_scores["neutral"] = max(0.3, 1 - total_emotion)
    
    # Normalize
    total = sum(emotion_scores.values())
    if total > 0:
        emotion_scores = {k: v/total for k, v in emotion_scores.items()}
    
    # Convert to API format
    return [{"label": emotion.upper(), "score": score} for emotion, score in emotion_scores.items()]

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_note(self, note_id, content):
    """
    Analyze emotion in note content using Hugging Face API with fallback
    """
    try:
        print(f"Processing note {note_id} with content length: {len(content)}")
        
        # Input validation
        if not content or len(content.strip()) == 0:
            raise ValueError("Content cannot be empty")
        
        # Truncate content if too long
        max_length = 500
        if len(content) > max_length:
            content = content[:max_length]
            print(f"Content truncated to {max_length} characters")
        
        emotion_data = None
        analysis_method = "unknown"
        
        # Try Hugging Face API first
        try:
            emotion_data = call_hf_emotion_api(content)
            analysis_method = "huggingface_api"
            print("Hugging Face API analysis successful")
            
        except Exception as e:
            print(f"Hugging Face API failed: {e}")
            
            # Check if we should retry (model loading, network issues)
            error_str = str(e).lower()
            if ("loading" in error_str or 
                "network" in error_str or 
                "timeout" in error_str or
                "connection" in error_str):
                if self.request.retries < self.max_retries:
                    print(f"Retrying due to recoverable error (attempt {self.request.retries + 1})")
                    raise self.retry(exc=e, countdown=60)
            
            # Fall back to keyword analysis
            print("Falling back to keyword analysis...")
            emotion_data = analyze_with_keywords_fallback(content)
            analysis_method = "keywords_fallback"
        
        # Process emotion scores
        emotion_scores = {}
        if emotion_data:
            for category in emotion_data:
                emotion = category["label"].lower()
                score = round(float(category["score"]), 3)
                if emotion in SUPPORTED_EMOTIONS:
                    emotion_scores[emotion] = score
        
        # Ensure we have all required emotions
        for emotion in SUPPORTED_EMOTIONS:
            if emotion not in emotion_scores:
                emotion_scores[emotion] = 0.0
        
        # Update the Note in the database
        try:
            note = Note.query.get(note_id)
            if not note:
                raise ValueError(f"Note with ID {note_id} not found")
            
            # Map emotion scores to database fields
            note.anger_value = emotion_scores.get('anger', 0.0)
            note.disgust_value = emotion_scores.get('disgust', 0.0)
            note.fear_value = emotion_scores.get('fear', 0.0)
            note.joy_value = emotion_scores.get('joy', 0.0)
            note.neutral_value = emotion_scores.get('neutral', 0.0)
            note.sadness_value = emotion_scores.get('sadness', 0.0)
            note.surprise_value = emotion_scores.get('surprise', 0.0)
            
            db.session.commit()
            print(f"Note {note_id} updated successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            raise
        
        # Find top emotion
        top_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        result_data = {
            "note_id": note_id,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "top_emotion": top_emotion[0],
            "top_confidence": float(top_emotion[1]),
            "all_emotions": emotion_scores,
            "analysis_method": analysis_method,
            "status": "success"
        }
        
        print(f"Task completed successfully for note {note_id} using {analysis_method}")
        return result_data
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in send_note task: {error_msg}")
        
        # For final failure, still try to update note with neutral values
        try:
            note = Note.query.get(note_id)
            if note:
                note.neutral_value = 1.0
                db.session.commit()
        except:
            pass
        
        return {
            "note_id": note_id,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "top_emotion": "neutral",
            "top_confidence": 1.0,
            "all_emotions": {"neutral": 1.0},
            "analysis_method": "error_fallback",
            "status": "error",
            "error_message": error_msg
        }
    
    finally:
        # Clean up memory
        gc.collect()

@shared_task
def process(x, y):
    """Simple test task"""
    i = 0
    while i < 5:
        sleep(1)
        i += 1
        print("Processing...")
    
    return x**2 + y**2

@shared_task
def health_check():
    """Health check task"""
    return {
        "status": "healthy",
        "timestamp": str(db.func.now())
    }