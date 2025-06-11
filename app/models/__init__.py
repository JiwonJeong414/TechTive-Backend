from app.models.note import Note, NoteSchema
from app.models.weekly_advice import WeeklyAdvice, WeeklyAdviceSchema
from app.models.user import User, UserSchema
from app.models.formatting import Formatting, FormattingSchema
from app.models.quote import Quote, QuoteSchema

# Define what should be available when using "from models import *"
__all__ = [
    'User', 'UserSchema',
    'Note', 'NoteSchema',
    'WeeklyAdvice', 'WeeklyAdviceSchema',
    'Formatting', 'FormattingSchema',
    'Quote', 'QuoteSchema'
]
