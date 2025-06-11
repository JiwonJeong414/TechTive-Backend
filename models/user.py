from marshmallow import validate
from extensions import db, ma

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)
    notes = db.relationship(
        "Note", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    weekly_advices = db.relationship(
        "WeeklyAdvice", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        """
        String representation of the User instance
        """
        return f"<User {self.id}>"
    
class UserSchema(ma.SQLAlchemySchema):
    """
    Marshmallow schema for serializing and deserializing User instances.

    Data Validation:
        - firebase_uid: Required and cannot be empty
    """

    class Meta:
        model = User

    id = ma.auto_field()
    firebase_uid = ma.auto_field(required=True, validate=validate.Length(min=1))