from flask import Blueprint, jsonify
from models.quote import Quote, QuoteSchema
from extensions import db
import random

quotes_bp = Blueprint('quotes', __name__, url_prefix='/api')
quote_schema = QuoteSchema()

@quotes_bp.route("/random/quotes/")
def get_random_quote():
    """Endpoint for getting a random quote from the database"""
    # Get total count of quotes
    quote_count = Quote.query.count()
    
    if quote_count == 0:
        # If no quotes in database, load them from CSV
        Quote.load_quotes_from_csv()
        quote_count = Quote.query.count()
        
    if quote_count == 0:
        return jsonify({"error": "No quotes found"}), 404
    
    # Get random quote
    random_offset = random.randint(0, quote_count - 1)
    random_quote = Quote.query.offset(random_offset).first()
    
    return jsonify(quote_schema.dump(random_quote))