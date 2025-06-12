from flask import Blueprint, jsonify, request
from app.models.note import Note, NoteSchema
from app.extensions import db
from app.auth.firebase_auth import firebase_auth_required

notes_bp = Blueprint('notes', __name__, url_prefix='/api')
note_schema = NoteSchema()

@notes_bp.route("/note/", methods=["POST"])
@firebase_auth_required
def create_note():
    """
    Endpoint for creating a note
    """
    # Validate Request 'content' and 'formattings' fields
    data = request.get_json()
    note = NoteSchema().load(data)
    
    # Add user_id from the authenticated user
    note.user_id = request.user.id
    
    # Create and save the note
    db.session.add(note)
    db.session.commit()
    
    return jsonify(note_schema.dump(note)), 201

