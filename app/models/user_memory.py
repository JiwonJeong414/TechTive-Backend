from marshmallow import validate
from app.extensions import db, ma

class UserMemory(db.Model):
    """
    Stores summarized memories of user's notes in batches for context building
    """
    __tablename__ = "user_memories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Memory content - summary of a batch of notes
    summary = db.Column(db.Text, nullable=False)
    
    # Metadata about the memory
    notes_count_in_batch = db.Column(db.Integer, nullable=False)
    first_note_date = db.Column(db.DateTime(timezone=True), nullable=False)
    last_note_date = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    
    # Dominant emotional themes in this batch
    dominant_emotion = db.Column(db.String(20), nullable=False)
    emotional_intensity = db.Column(db.Float, default=0.0)  # 0-1 scale
    
    # Keywords/themes extracted from this batch
    themes = db.Column(db.Text, nullable=True)  # JSON string of themes

    def __repr__(self):
        return f"<Memory {self.id} for User {self.user_id} - {self.dominant_emotion}>"

class UserMemorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = UserMemory
        load_instance = True

    id = ma.auto_field(dump_only=True)
    user_id = ma.auto_field(dump_only=True)
    summary = ma.auto_field(dump_only=True)
    notes_count_in_batch = ma.auto_field(dump_only=True)
    first_note_date = ma.DateTime(dump_only=True)
    last_note_date = ma.DateTime(dump_only=True)
    created_at = ma.DateTime(dump_only=True)
    dominant_emotion = ma.auto_field(dump_only=True)
    emotional_intensity = ma.auto_field(dump_only=True)
    themes = ma.auto_field(dump_only=True)
