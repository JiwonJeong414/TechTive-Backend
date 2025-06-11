from marshmallow import validate, fields
from app.extensions import db, ma
import enum

class FormattingType(enum.Enum):
    HEADER = "header"
    BOLD = "bold"
    ITALIC = "italic"

class Formatting(db.Model):
    """
    Formatting for the content of a Note
    """
    __tablename__ = "formatting"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.id"), nullable=False) # one-to-many each note can have many formatting
    
    # Formatting type (header, bold, italic)
    type = db.Column(db.Enum(FormattingType), nullable=False)
    
    # Range information
    location = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Formatting {self.id} for Note {self.note_id}>"

class FormattingSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Formatting
        load_instance = True

    id = ma.auto_field(dump_only=True)
    note_id = ma.auto_field(dump_only=True)
    type = fields.Enum(FormattingType, required=True)
    location = ma.auto_field(required=True, validate=validate.Range(min=0))
    length = ma.auto_field(required=True, validate=validate.Range(min=1))