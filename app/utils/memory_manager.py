import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.models.note import Note
from app.models.user_memory import UserMemory
from app.models.weekly_advice import WeeklyAdvice
from app.extensions import db
from app.config import config
from app.utils.api_utils import create_memory_summary

class MemoryManager:
    """Manages user memories and context building for advice generation"""
    
    NOTES_PER_MEMORY = 3  # Create memory summary every 3 notes
    MAX_MEMORIES_FOR_ADVICE = 5  # Use last 5 memories for context
    RECENT_NOTES_FOR_ADVICE = 3  # Use last 3 notes directly
    
    @staticmethod
    def should_create_memory(user_id: int) -> bool:
        """Check if we should create a new memory from recent notes"""
        # Get last memory
        last_memory = UserMemory.query.filter_by(user_id=user_id)\
            .order_by(UserMemory.created_at.desc()).first()
        
        if not last_memory:
            # First memory after reaching threshold
            total_notes = Note.query.filter_by(user_id=user_id).count()
            return total_notes >= MemoryManager.NOTES_PER_MEMORY
        
        # Count notes since last memory
        notes_since_memory = Note.query.filter_by(user_id=user_id)\
            .filter(Note.created_at > last_memory.created_at).count()
        
        return notes_since_memory >= MemoryManager.NOTES_PER_MEMORY
    
    @staticmethod
    def get_notes_for_memory(user_id: int) -> List[Note]:
        """Get notes that should be processed into the next memory"""
        last_memory = UserMemory.query.filter_by(user_id=user_id)\
            .order_by(UserMemory.created_at.desc()).first()
        
        query = Note.query.filter_by(user_id=user_id)
        
        if last_memory:
            query = query.filter(Note.created_at > last_memory.created_at)
        
        return query.order_by(Note.created_at.asc())\
            .limit(MemoryManager.NOTES_PER_MEMORY).all()
    
    @staticmethod
    def analyze_notes_batch(notes: List[Note]) -> Tuple[str, float, str]:
        """Analyze a batch of notes to extract dominant emotion and themes"""
        if not notes:
            return "neutral", 0.0, ""
        
        # Calculate average emotions
        emotions = {
            'joy': sum(note.joy_value for note in notes) / len(notes),
            'sadness': sum(note.sadness_value for note in notes) / len(notes),
            'anger': sum(note.anger_value for note in notes) / len(notes),
            'fear': sum(note.fear_value for note in notes) / len(notes),
            'neutral': sum(note.neutral_value for note in notes) / len(notes),
            'disgust': sum(note.disgust_value for note in notes) / len(notes),
            'surprise': sum(note.surprise_value for note in notes) / len(notes)
        }
        
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])
        
        return dominant_emotion[0], dominant_emotion[1], ""
    
    @staticmethod
    def create_and_save_memory(user_id: int) -> Optional[UserMemory]:
        """Create and save a new memory from recent notes"""
        try:
            notes = MemoryManager.get_notes_for_memory(user_id)
            
            if len(notes) < MemoryManager.NOTES_PER_MEMORY:
                return None
            
            # Create summary
            summary = create_memory_summary(notes)
            
            # Analyze batch
            dominant_emotion, intensity, themes = MemoryManager.analyze_notes_batch(notes)
            
            # Create memory record
            memory = UserMemory(
                user_id=user_id,
                summary=summary,
                notes_count_in_batch=len(notes),
                first_note_date=notes[0].created_at,
                last_note_date=notes[-1].created_at,
                dominant_emotion=dominant_emotion,
                emotional_intensity=intensity,
                themes=themes
            )
            
            db.session.add(memory)
            db.session.commit()
            
            print(f"Created memory {memory.id} for user {user_id}: {summary[:50]}...")
            return memory
            
        except Exception as e:
            print(f"Error creating memory for user {user_id}: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_context_for_advice(user_id: int) -> Dict:
        """Get memories + recent notes for advice generation"""
        # Get recent memories (excluding current batch being processed)
        memories = UserMemory.query.filter_by(user_id=user_id)\
            .order_by(UserMemory.created_at.desc())\
            .limit(MemoryManager.MAX_MEMORIES_FOR_ADVICE).all()
        
        # Get most recent notes (not yet in memory)
        recent_notes = Note.query.filter_by(user_id=user_id)\
            .order_by(Note.created_at.desc())\
            .limit(MemoryManager.RECENT_NOTES_FOR_ADVICE).all()
        
        # Calculate current emotional state from recent notes
        current_emotions = {}
        if recent_notes:
            emotions_sum = {
                'joy': sum(note.joy_value for note in recent_notes),
                'sadness': sum(note.sadness_value for note in recent_notes),
                'anger': sum(note.anger_value for note in recent_notes),
                'fear': sum(note.fear_value for note in recent_notes),
                'neutral': sum(note.neutral_value for note in recent_notes)
            }
            
            for emotion, total in emotions_sum.items():
                current_emotions[emotion] = total / len(recent_notes)
        
        return {
            'memories': memories,
            'recent_notes': recent_notes,
            'current_emotions': current_emotions,
            'dominant_current_emotion': max(current_emotions.items(), key=lambda x: x[1])[0] if current_emotions else 'neutral'
        }