from flask import render_template
from flask_login import login_required, current_user
from app.main import main_bp
from app.models import Transaction, Goal
from analytics import FinanceAnalytics


@main_bp.route('/')
@login_required
def dashboard():
    transactions = [
        {
            'id': t.id, 'type': t.type, 'category': t.category.name if t.category else 'Uncategorized',
            'amount': float(t.amount), 'description': t.description, 'date': str(t.date)
        }
        for t in Transaction.query.filter_by(user_id=current_user.id).all()
    ]

    analytics = FinanceAnalytics(transactions)
    return render_template(
        'dashboard.html',
        summary=analytics.get_summary(),
        monthly_trends=analytics.get_monthly_trends(),
        category_breakdown=analytics.get_category_breakdown(),
        saving_opportunities=analytics.get_saving_opportunities(),
        recent_transactions=sorted(transactions, key=lambda x: x['date'], reverse=True)[:10],
    )
