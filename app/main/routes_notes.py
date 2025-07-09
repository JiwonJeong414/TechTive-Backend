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

