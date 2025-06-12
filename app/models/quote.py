from marshmallow import validate
from app.extensions import db, ma

class Quote(db.Model):
    """
    Model for storing inspirational quotes with their authors
    """
    __tablename__ = "quote_list"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Quote: {self.content[:50]}... by {self.author}>"

class QuoteSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Quote
        load_instance = True

    id = ma.auto_field(dump_only=True)
    content = ma.auto_field()
    author = ma.auto_field()