import requests
import json
from typing import List, Optional, Dict
from datetime import datetime, timezone
from app.models.note import Note
from app.models.weekly_advice import WeeklyAdvice
from app.extensions import db
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

def create_memory_summary(notes: List[Note]) -> str:
    """Use OpenAI to create a concise summary of a batch of notes"""
    try:
        api_token = config.OPENAI_API_KEY
        
        # Prepare notes content for summarization
        notes_content = []
        for i, note in enumerate(notes, 1):
            # Get emotion info
            emotions = {
                'joy': note.joy_value,
                'sadness': note.sadness_value,
                'anger': note.anger_value,
                'fear': note.fear_value,
                'neutral': note.neutral_value
            }
            dominant = max(emotions.items(), key=lambda x: x[1])
            
            notes_content.append(f"Note {i} (mostly {dominant[0]}): {note.content[:200]}")
        
        prompt = f"""Summarize these {len(notes)} journal entries into a concise memory summary that is specific (2-3 sentences max).

                    Notes to summarize:
                    {chr(10).join(notes_content)}

                    Create a memory summary that captures the essence of this period:"""

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI that creates concise memory summaries of journal entries. Focus on emotional patterns and key themes."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
        
        return ""
        
    except Exception as e:
        print(f"Error creating memory summary: {e}")
        return ""

def generate_and_save_advice(user_id: int) -> Optional[WeeklyAdvice]:
    """Generate and save new advice using memories + recent notes"""
    try:
        from app.utils.memory_manager import MemoryManager
        
        # Validate API key
        api_token = config.OPENAI_API_KEY
        if not api_token:
            raise Exception("OPENAI_API_KEY not configured in environment variables")
        
        # First, create memory if needed
        if MemoryManager.should_create_memory(user_id):
            MemoryManager.create_and_save_memory(user_id)
        
        # Get context for advice
        context = MemoryManager.get_context_for_advice(user_id)
        
        if not context['recent_notes'] and not context['memories']:
            raise Exception("No notes or memories available for advice generation")
        
        # Build prompt with memories and recent notes
        prompt_parts = [
            "You are an empathetic AI counselor. Generate personalized advice (2-3 sentences) based on the user's journal history and current state. Be specific.",
            "",
            f"CURRENT EMOTIONAL STATE: {context['dominant_current_emotion']}",
            ""
        ]
        
        # Add memories for context
        if context['memories']:
            prompt_parts.append("MEMORY CONTEXT (past emotional patterns):")
            for i, memory in enumerate(context['memories'], 1):
                prompt_parts.append(f"{i}. {memory.summary} (dominant: {memory.dominant_emotion})")
            prompt_parts.append("")
        
        # Add recent notes for immediate context
        if context['recent_notes']:
            prompt_parts.append("RECENT NOTES (current situation):")
            for i, note in enumerate(context['recent_notes'], 1):
                # Get dominant emotion for this note
                note_emotions = {
                    'joy': note.joy_value, 'sadness': note.sadness_value,
                    'anger': note.anger_value, 'fear': note.fear_value,
                    'neutral': note.neutral_value
                }
                dominant = max(note_emotions.items(), key=lambda x: x[1])[0]
                
                prompt_parts.append(f"{i}. [{dominant}] {note.content}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Based on the memory context and recent notes, provide specific supportive advice.",
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Call OpenAI API
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an empathetic AI counselor who provides personalized advice based on journal analysis and emotional patterns."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
            "temperature": 0.8
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API request failed with status {response.status_code}")
        
        result = response.json()
        if "choices" not in result or len(result["choices"]) == 0:
            raise Exception("Invalid OpenAI API response format")
        
        advice_content = result["choices"][0]["message"]["content"].strip()
        
        if not advice_content:
            raise Exception("No advice content generated")
        
        # Save advice with context metadata
        advice = WeeklyAdvice(
            user_id=user_id,
            content=advice_content,
            trigger_type="note_count",
            memories_used_count=len(context['memories']),
            recent_notes_used_count=len(context['recent_notes']),
            dominant_emotion=context['dominant_current_emotion'],
            notes_analyzed_count=Note.query.filter_by(user_id=user_id).count()
        )
        
        db.session.add(advice)
        db.session.commit()
        
        return advice
        
    except Exception as e:
        print(f"Error generating advice for user {user_id}: {e}")
        db.session.rollback()
        raise Exception(f"Failed to generate advice for user {user_id}: {str(e)}")
    

def should_generate_advice(user_id: int) -> bool:
    """
    Determine if advice should be generated for user
    Current logic: Every 3 notes since last advice
    """
    try:
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
        
    except Exception as e:
        print(f"Error checking advice eligibility for user {user_id}: {e}")
        return False