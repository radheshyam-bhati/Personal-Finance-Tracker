from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import date, datetime
from app.analytics import analytics_bp
from app.analytics.services import FinanceAnalytics
from app.models import Goal

@analytics_bp.route('/')
@login_required
def index():
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
    monthly_trends = analytics.get_monthly_trends(12)
    category_breakdown = analytics.get_category_breakdown(start_date, end_date)
    saving_opportunities = analytics.get_saving_opportunities(start_date, end_date)
    spending_patterns = analytics.get_spending_patterns(start_date, end_date)
    savings_rate = analytics.get_savings_rate(start_date, end_date)
    projections = analytics.get_projections()
    
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.target_date).all()
    goals_progress = [analytics.get_goal_progress(g) for g in goals]
    
    return render_template('analytics/index.html',
                         summary=summary,
                         monthly_trends=monthly_trends,
                         category_breakdown=category_breakdown,
                         saving_opportunities=saving_opportunities,
                         spending_patterns=spending_patterns,
                         savings_rate=savings_rate,
                         projections=projections,
                         goals=list(zip(goals, goals_progress)),
                         start_date=start_date,
                         end_date=end_date)

@analytics_bp.route('/api/chart-data')
@login_required
def chart_data():
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
    
    monthly_data = analytics.get_monthly_chart_data(12)
    category_data = analytics.get_category_chart_data(start_date, end_date)
    
    return jsonify({
        'monthly': monthly_data,
        'category': category_data
    })

@analytics_bp.route('/api/spending-patterns')
@login_required
def spending_patterns_api():
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
    
    patterns = analytics.get_spending_patterns(start_date, end_date)
    return jsonify(patterns)

@analytics_bp.route('/api/category-trends')
@login_required
def category_trends_api():
    analytics = FinanceAnalytics(current_user.id)
    months = request.args.get('months', 6, type=int)
    trends = analytics.get_category_trends(months)
    return jsonify(trends)