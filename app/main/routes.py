from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.main import main_bp
from app.analytics.services import FinanceAnalytics
from app.models import Transaction, Goal, Category
from datetime import date, datetime

@main_bp.route('/')
@login_required
def dashboard():
    analytics = FinanceAnalytics(current_user.id)
    
    start_date = None
    end_date = None
    if request.args.get('start_date'):
        try:
            start_date = datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
        except:
            pass
    if request.args.get('end_date'):
        try:
            end_date = datetime.strptime(request.args['end_date'], '%Y-%m-%d').date()
        except:
            pass
    
    summary = analytics.get_summary(start_date, end_date)
    monthly_trends = analytics.get_monthly_trends(6)
    category_breakdown = analytics.get_category_breakdown(start_date, end_date)
    saving_opportunities = analytics.get_saving_opportunities(start_date, end_date)
    savings_rate = analytics.get_savings_rate(start_date, end_date)
    projections = analytics.get_projections()
    
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.date.desc(), Transaction.id.desc()
    ).limit(5).all()
    
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.target_date).all()
    goals_progress = [analytics.get_goal_progress(g) for g in goals]
    
    return render_template('main/dashboard.html',
                         summary=summary,
                         monthly_trends=monthly_trends,
                         category_breakdown=category_breakdown,
                         saving_opportunities=saving_opportunities,
                         savings_rate=savings_rate,
                         projections=projections,
                         recent_transactions=recent_transactions,
                         goals=list(zip(goals, goals_progress)),
                         start_date=start_date,
                         end_date=end_date)

@main_bp.route('/health')
def health():
    return {'status': 'ok'}, 200