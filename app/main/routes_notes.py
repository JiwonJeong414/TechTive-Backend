from flask import Blueprint, jsonify, request
from app.models.note import Note, NoteSchema
from app.extensions import db
from app.auth.firebase_auth import firebase_auth_required
from app.utils.tasks import send_note
from celery.result import AsyncResult

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
    
    # Start emotion analysis task asynchronously
    if note.content:
        emotion_task = send_note.delay(note.id, note.content)
        print(f"Started emotion analysis task with ID: {emotion_task.id}")
    
    return jsonify(note_schema.dump(note)), 201


@notes_bp.route("/note/<int:note_id>/", methods=["GET"])
@firebase_auth_required
def get_note(note_id):
    """
    Endpoint for getting an individual note with sentiment analysis
    """
    # Find the note by ID
    note = Note.query.get(note_id)
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    # Check if the user owns this note
    if note.user_id != request.user.id:
        return jsonify({"error": "Unauthorized to access this note"}), 403
    
    # Return the note with sentiment analysis
    return jsonify(note_schema.dump(note)), 200


@notes_bp.route("/note/", methods=["GET"])
@firebase_auth_required
def get_user_notes():
    """
    Endpoint for getting all notes for the authenticated user (without sentiment analysis)
    """
    # Get all notes for the authenticated user
    notes = Note.query.filter_by(user_id=request.user.id).order_by(Note.created_at).all()
    
    # Create a simplified schema for listing (without sentiment analysis)
    notes_list = []
    for note in notes:
        note_data = {
            "id": note.id,
            "content": note.content,
            "created_at": note.created_at.isoformat() if note.created_at else None
        }
        
        notes_list.append(note_data)
    
    return jsonify({"notes": notes_list}), 200


@notes_bp.route("/note/<int:note_id>/", methods=["PUT"])
@firebase_auth_required
def update_note(note_id):
    """
    Endpoint for updating a note
    """
    # Find the note by ID
    note = Note.query.get(note_id)
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    # Check if the user owns this note
    if note.user_id != request.user.id:
        return jsonify({"error": "Unauthorized to update this note"}), 403
    
    # Validate and load the update data
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Content field is required"}), 400
    
    # Update the note content
    note.content = data['content']
    
    # Save the changes
    db.session.commit()
    
    # Start new emotion analysis task asynchronously
    if note.content:
        emotion_task = send_note.delay(note.id, note.content)
        print(f"Started emotion analysis task for update with ID: {emotion_task.id}")
    
    return jsonify(note_schema.dump(note)), 200


@notes_bp.route("/note/<int:note_id>/", methods=["DELETE"])
@firebase_auth_required
def delete_note(note_id):
    """
    Endpoint for deleting a note
    """
    # Find the note by ID
    note = Note.query.get(note_id)
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    # Check if the user owns this note
    if note.user_id != request.user.id:
        return jsonify({"error": "Unauthorized to delete this note"}), 403
    
    # Delete the note (cascade will handle related formattings)
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({"message": "Note deleted successfully"}), 200


@notes_bp.route("/task/<task_id>/", methods=["GET"])
@firebase_auth_required
def get_task_status(task_id):
    """
    Endpoint for checking the status of a Celery task
    """
    task_result = AsyncResult(task_id)
    
    if task_result.ready():
        if task_result.successful():
            return jsonify({
                "task_id": task_id,
                "status": "completed",
                "result": task_result.result
            }), 200
        else:
            return jsonify({
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.info)
            }), 400
    else:
        return jsonify({
            "task_id": task_id,
            "status": "pending"
        }), 202
