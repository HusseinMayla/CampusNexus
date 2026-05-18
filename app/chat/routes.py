from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
def chat_home():
    return "Chat Home"
