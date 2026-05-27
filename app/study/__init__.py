from flask import Blueprint

study_bp = Blueprint('study', __name__)

from app.study import routes  # noqa
