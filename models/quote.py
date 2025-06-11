from marshmallow import validate
from extensions import db, ma
import csv
import os

class Quote(db.Model):
    """
    Model for storing inspirational quotes with their authors
    """
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Quote: {self.content[:50]}... by {self.author}>"
    
    @classmethod
    def load_quotes_from_csv(cls):
        """Load quotes from the CSV file into the database"""
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'quotes_author.csv')
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Check if quote already exists to avoid duplicates
                existing_quote = cls.query.filter_by(content=row['Quote']).first()
                if not existing_quote:
                    quote = cls(
                        content=row['Quote'],
                        author=row['Author']
                    )
                    db.session.add(quote)
        
        db.session.commit()

class QuoteSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Quote
        load_instance = True

    id = ma.auto_field()
    content = ma.auto_field()
    author = ma.auto_field()