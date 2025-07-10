from marshmallow import validate
from app.extensions import db, ma

class WeeklyAdvice(db.Model):
    """
    Advice for user based on their emotional patterns and notes
    """
    __tablename__ = "weekly_advices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    
    # Track what triggered this advice
    trigger_type = db.Column(db.String(50), nullable=False, default="note_count")  # "note_count", "emotional_pattern", "manual"
    notes_analyzed_count = db.Column(db.Integer, default=0)
    
    # Emotional context when advice was generated
    avg_joy = db.Column(db.Float, default=0.0)
    avg_sadness = db.Column(db.Float, default=0.0)
    avg_anger = db.Column(db.Float, default=0.0)
    avg_fear = db.Column(db.Float, default=0.0)
    avg_neutral = db.Column(db.Float, default=0.0)
    
    # For backwards compatibility - can be removed in future migration
    of_week = db.Column(db.DateTime(timezone=True), nullable=True)

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
    avg_joy = ma.auto_field(dump_only=True)
    avg_sadness = ma.auto_field(dump_only=True)
    avg_anger = ma.auto_field(dump_only=True)
    avg_fear = ma.auto_field(dump_only=True)
    avg_neutral = ma.auto_field(dump_only=True)
