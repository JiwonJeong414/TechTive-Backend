"""
Main package for route blueprints and application logic.
This package contains all the route modules and their associated blueprints.
"""

from flask import Blueprint

# Import blueprints here to make them available when importing from main
from .routes_quotes import quotes_bp
from .routes_notes import notes_bp
from .routes_advice import advice_bp

# List of all blueprints that can be registered with the app
blueprints = [
    quotes_bp,
    notes_bp,
    advice_bp
] 