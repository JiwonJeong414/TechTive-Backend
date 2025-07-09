import gc
import os
from time import sleep
from celery import shared_task
from app.models.note import Note
from app.extensions import db
from app.config import config
from app.utils.api_utils import call_hf_emotion_api

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

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_note(self, note_id, content):
    """
    Analyze emotion in note content using Hugging Face API
    """
    try:
        # Input validation
        if not content or len(content.strip()) == 0:
            raise ValueError("Content cannot be empty")
        
        # Call Hugging Face API
        emotion_data = call_hf_emotion_api(content)
        
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
            
        except Exception as e:
            db.session.rollback()
            raise
        
        result_data = {
            "note_id": note_id,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "all_emotions": emotion_scores,
            "status": "success"
        }
    
        return result_data
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if we should retry (model loading, network issues)
        error_str = error_msg.lower()
        if ("loading" in error_str or 
            "network" in error_str or 
            "timeout" in error_str or
            "connection" in error_str):
            if self.request.retries < self.max_retries:
                print(f"Retrying due to recoverable error (attempt {self.request.retries + 1})")
                raise self.retry(exc=e, countdown=60)
        
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
            "all_emotions": {"neutral": 1.0},
            "status": "error",
            "error_message": error_msg
        }
    
    finally:
        # Clean up memory
        gc.collect()

@shared_task
def health_check():
    """Health check task"""
    return {
        "status": "healthy",
        "timestamp": str(db.func.now())
    }