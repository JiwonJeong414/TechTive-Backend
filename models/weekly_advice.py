from marshmallow import validate
from extensions import db, ma

class WeeklyAdvice(db.Model):
    """
    Weekly Advice for user
    """
    __tablename__ = "weekly_advices"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False) # db.Text is more large string values
    created_at = db.Column(db.DateTime(timezone=True), default=db.func.now())
    of_week = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Weekly Advice {self.id} for User {self.user_id} of Week {self.of_week}>"
    
class WeeklyAdviceSchema(ma.SQLAlchemySchema):
    class Meta:
        model = WeeklyAdvice
        load_instance = True

    id = ma.auto_field(dump_only=True)
    user_id = ma.auto_field(dump_only=True)
    content = ma.auto_field(required=True, validate=validate.Length(min=1))
    created_at = ma.DateTime(dump_only=True)
    of_week = ma.DateTime(required=True)