import requests
from typing import Dict, List, Optional
from app.config import config
from app.models.note import Note
from app.models.weekly_advice import WeeklyAdvice
from app.extensions import db
from datetime import datetime, timedelta

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

def should_generate_advice(user_id: int) -> bool:
    """
    Determine if advice should be generated for user
    Current logic: Every 3 notes since last advice
    """
    # Get last advice
    last_advice = WeeklyAdvice.query.filter_by(user_id=user_id)\
        .order_by(WeeklyAdvice.created_at.desc()).first()
    
    # Get total notes count
    total_notes = Note.query.filter_by(user_id=user_id).count()
    
    if not last_advice:
        # First advice after 3 notes
        return total_notes >= 3
    
    # Count notes since last advice
    notes_since_advice = Note.query.filter_by(user_id=user_id)\
        .filter(Note.created_at > last_advice.created_at).count()
    
    return notes_since_advice >= 3

def get_emotional_summary(user_id: int, limit: int = 10) -> Dict[str, float]:
    """Get average emotional scores from recent notes"""
    recent_notes = Note.query.filter_by(user_id=user_id)\
        .order_by(Note.created_at.desc())\
        .limit(limit).all()
    
    if not recent_notes:
        return {
            'joy': 0.0, 'sadness': 0.0, 'anger': 0.0,
            'fear': 0.0, 'neutral': 0.0, 'disgust': 0.0, 'surprise': 0.0
        }
    
    # Calculate averages
    emotions = {
        'joy': sum(note.joy_value for note in recent_notes) / len(recent_notes),
        'sadness': sum(note.sadness_value for note in recent_notes) / len(recent_notes),
        'anger': sum(note.anger_value for note in recent_notes) / len(recent_notes),
        'fear': sum(note.fear_value for note in recent_notes) / len(recent_notes),
        'neutral': sum(note.neutral_value for note in recent_notes) / len(recent_notes),
        'disgust': sum(note.disgust_value for note in recent_notes) / len(recent_notes),
        'surprise': sum(note.surprise_value for note in recent_notes) / len(recent_notes)
    }
    
    return emotions

def generate_and_save_advice(user_id: int) -> Optional[WeeklyAdvice]:
    """Generate and save new advice for user"""
    try:
        # Validate API key is configured
        api_token = config.OPENAI_API_KEY
        if not api_token:
            raise Exception("OPENAI_API_KEY not configured in environment variables")
        
        # Get emotional summary
        emotions = get_emotional_summary(user_id)
        notes_count = Note.query.filter_by(user_id=user_id).count()
        
        # Find dominant emotions
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])
        
        # Generate prompt inline
        prompt = f"""Based on emotional analysis of {notes_count} recent journal entries, provide personalized advice in 2-3 sentences.

Emotional Profile:
- Joy: {emotions['joy']:.2f}
- Sadness: {emotions['sadness']:.2f}
- Anger: {emotions['anger']:.2f}
- Fear: {emotions['fear']:.2f}
- Neutral: {emotions['neutral']:.2f}

Dominant emotion: {dominant_emotion[0]} ({dominant_emotion[1]:.2f})

Provide supportive, actionable advice that:
1. Acknowledges their emotional state
2. Offers practical coping strategies
3. Encourages positive habits

Keep it concise (2-3 sentences) and empathetic."""
        
        # Call OpenAI API to generate advice
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        api_url = "https://api.openai.com/v1/chat/completions"
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a supportive and empathetic AI assistant that provides personalized advice based on emotional analysis of journal entries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API request failed with status {response.status_code}")
        
        result = response.json()
        if "choices" not in result or len(result["choices"]) == 0:
            raise Exception("Invalid OpenAI API response format")
        
        advice_content = result["choices"][0]["message"]["content"].strip()
        
        if not advice_content:
            raise Exception("No advice content generated")
        
        # Save to database
        advice = WeeklyAdvice(
            user_id=user_id,
            content=advice_content,
            trigger_type="note_count",
            notes_analyzed_count=notes_count,
            avg_joy=emotions['joy'],
            avg_sadness=emotions['sadness'],
            avg_anger=emotions['anger'],
            avg_fear=emotions['fear'],
            avg_neutral=emotions['neutral']
        )
        
        db.session.add(advice)
        db.session.commit()
        
        return advice
        
    except Exception as e:
        print(f"Error generating advice for user {user_id}: {e}")
        db.session.rollback()
        # Re-raise the exception with more context instead of returning None
        raise Exception(f"Failed to generate advice for user {user_id}: {str(e)}") 