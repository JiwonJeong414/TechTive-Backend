from marshmallow import validate
from app.extensions import db, ma

class WeeklyAdvice(db.Model):
    """
    Advice for user based on their emotional patterns, recent notes, and memories
    """
    __tablename__ = "weekly_advices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    
    # Track what triggered this advice
    trigger_type = db.Column(db.String(50), nullable=False, default="note_count")
    
    # Context used for advice generation
    memories_used_count = db.Column(db.Integer, default=0)
    recent_notes_used_count = db.Column(db.Integer, default=0)
    dominant_emotion = db.Column(db.String(20), nullable=True)
    
    # For backwards compatibility
    notes_analyzed_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Advice {self.id} for User {self.user_id} - {self.trigger_type}>"

    
class WeeklyAdviceSchema(ma.SQLAlchemySchema):
    class Meta:
        model = WeeklyAdvice
        load_instance = True

    id = ma.auto_field(dump_only=True)
    user_id = ma.auto_field(dump_only=True)
    content = ma.auto_field(required=True, validate=validate.Length(min=1))
    created_at = ma.DateTime(dump_only=True)
    trigger_type = ma.auto_field(dump_only=True)
    notes_analyzed_count = ma.auto_field(dump_only=True)
