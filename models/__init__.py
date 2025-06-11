from .note import Note, NoteSchema
from .weekly_advice import WeeklyAdvice, WeeklyAdviceSchema
from .user import User, UserSchema
from .formatting import Formatting, FormattingSchema
from .quote import Quote, QuoteSchema

# Define what should be available when using "from models import *"
__all__ = [
    'User', 'UserSchema',
    'Note', 'NoteSchema',
    'WeeklyAdvice', 'WeeklyAdviceSchema',
    'Formatting', 'FormattingSchema',
    'Quote', 'QuoteSchema'
]
