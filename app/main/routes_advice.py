from flask import Blueprint, jsonify, request
from app.models.weekly_advice import WeeklyAdvice, WeeklyAdviceSchema
from app.extensions import db
from app.auth.firebase_auth import firebase_auth_required
from app.utils.api_utils import should_generate_advice
from app.utils.tasks import generate_advice_task

advice_bp = Blueprint('advice', __name__, url_prefix='/api')
advice_schema = WeeklyAdviceSchema()

@advice_bp.route("/advice/latest/", methods=["GET"])
@firebase_auth_required
def get_latest_advice():
    """Get the most recent advice for the authenticated user"""
    latest_advice = WeeklyAdvice.query.filter_by(user_id=request.user.id)\
        .order_by(WeeklyAdvice.created_at.desc()).first()
    
    if not latest_advice:
        return jsonify({"message": "No advice available yet"}), 404
    
    return jsonify(advice_schema.dump(latest_advice)), 200

@advice_bp.route("/advice/", methods=["GET"])
@firebase_auth_required
def get_user_advice_history():
    """Get all advice for the authenticated user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    advice_query = WeeklyAdvice.query.filter_by(user_id=request.user.id)\
        .order_by(WeeklyAdvice.created_at.desc())
    
    advice_pagination = advice_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "advice": [advice_schema.dump(advice) for advice in advice_pagination.items],
        "total": advice_pagination.total,
        "pages": advice_pagination.pages,
        "current_page": page
    }), 200

@advice_bp.route("/advice/generate/", methods=["POST"])
@firebase_auth_required
def generate_advice_manually():
    """Manually trigger advice generation"""
    try:
        # Check if user has any notes
        from app.models.note import Note
        notes_count = Note.query.filter_by(user_id=request.user.id).count()
        
        if notes_count == 0:
            return jsonify({"error": "No notes available for advice generation"}), 400
        
        # Generate advice asynchronously
        task = generate_advice_task.delay(request.user.id)
        
        return jsonify({
            "message": "Advice generation started",
            "task_id": task.id
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@advice_bp.route("/advice/check/", methods=["GET"])
@firebase_auth_required
def check_advice_eligibility():
    """Check if user is eligible for new advice"""
    should_generate = should_generate_advice(request.user.id)
    
    return jsonify({
        "eligible_for_advice": should_generate,
        "user_id": request.user.id
    }), 200

@advice_bp.route("/memory/", methods=["GET"])
@firebase_auth_required
def get_user_memories():
    """Get all memories for the authenticated user"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    from app.models.user_memory import UserMemory, UserMemorySchema
    
    memory_query = UserMemory.query.filter_by(user_id=request.user.id)\
        .order_by(UserMemory.created_at.desc())
    
    memory_pagination = memory_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    memory_schema = UserMemorySchema()
    
    return jsonify({
        "memories": [memory_schema.dump(memory) for memory in memory_pagination.items],
        "total": memory_pagination.total,
        "pages": memory_pagination.pages,
        "current_page": page
    }), 200