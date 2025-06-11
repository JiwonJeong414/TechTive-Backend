from .user import User, UserSchema
from .note import Note, NoteSchema
from .weekly_advice import WeeklyAdvice, WeeklyAdviceSchema
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
