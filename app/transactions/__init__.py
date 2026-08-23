from flask import Blueprint

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

from app.transactions import routes