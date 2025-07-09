from time import sleep
import gc
import os
from celery import shared_task
from app.models.note import Note
from app.extensions import db

# Disable transformers logging to reduce memory usage
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

def get_emotion_pipe():
    """
    Safely get the emotion classification pipeline with proper error handling
    """
    try:
        from transformers import pipeline
        # Use a smaller, more stable model
        pipe = pipeline(
            "text-classification", 
            model="j-hartmann/emotion-english-distilroberta-base",
            device=-1,  # Force CPU usage to avoid GPU memory issues
            return_all_scores=True
        )
        return pipe
    except Exception as e:
        print(f"Error loading emotion pipeline: {str(e)}")
        return None

@shared_task
def process(x, y):
    i = 0
    while i < 5:
        sleep(1)
        i += 1
        print("Processing...")
    
    return x**2 + y**2

@shared_task
def send_note(note_id, content):
    """
    Send content to Hugging Face API for emotion classification and update the Note in the database.
    Args:
        note_id (int): The ID of the note to update
        content (str): The text content to analyze for emotion
    Returns:
        dict: Emotion classification result with all emotion scores
    """
    emotion_pipe = None
    try:
        # Get the pipeline safely
        emotion_pipe = get_emotion_pipe()
        if not emotion_pipe:
            raise Exception("Failed to load emotion classification pipeline")
        
        # Limit content length to prevent memory issues
        if len(content) > 1000:
            content = content[:1000]
        
        # Perform emotion classification
        result = emotion_pipe(content, truncation=True, max_length=512)
        
        # Process results safely
        if result and len(result) > 0:
            emotions = result[0] if isinstance(result, list) else result
            emotion_scores = {emotion['label']: float(emotion['score']) for emotion in emotions}
        else:
            emotion_scores = {}
        
        # Update the Note in the database
        note = Note.query.get(note_id)
        if note:
            note.anger_value = emotion_scores.get('anger', 0.0)
            note.disgust_value = emotion_scores.get('disgust', 0.0)
            note.fear_value = emotion_scores.get('fear', 0.0)
            note.joy_value = emotion_scores.get('joy', 0.0)
            note.neutral_value = emotion_scores.get('neutral', 0.0)
            note.sadness_value = emotion_scores.get('sadness', 0.0)
            note.surprise_value = emotion_scores.get('surprise', 0.0)
            db.session.commit()
        
        # Find top emotion
        top_emotion = max(emotion_scores.items(), key=lambda x: x[1]) if emotion_scores else ("unknown", 0.0)
        
        return {
            "note_id": note_id,
            "content": content,
            "top_emotion": top_emotion[0],
            "top_confidence": top_emotion[1],
            "all_emotions": emotion_scores,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in emotion classification: {str(e)}")
        return {
            "note_id": note_id,
            "content": content,
            "top_emotion": "error",
            "top_confidence": 0.0,
            "all_emotions": {},
            "status": "error",
            "error_message": str(e)
        }
    finally:
        # Clean up memory
        if emotion_pipe:
            del emotion_pipe
        gc.collect()
    