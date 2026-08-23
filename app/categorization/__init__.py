from flask import Blueprint

categorization_bp = Blueprint('categorization', __name__, url_prefix='/categories')

from app.categorization import routes