from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import date, datetime, timedelta
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
    period_comparison = analytics.get_period_comparison(start_date, end_date)
    insights = analytics.generate_insights(start_date, end_date)
    savings_rate = analytics.get_savings_rate(start_date, end_date)
    
    # Calculate category changes vs previous period
    category_changes = []
    if category_breakdown['expense']:
        prev_breakdown = analytics.get_category_breakdown(
            start_date - timedelta(days=30) if start_date else None,
            end_date - timedelta(days=30) if end_date else None,
            type_filter='expense'
        )
        prev_category_map = {item['category']: item['amount'] for item in prev_breakdown['expense']}
        
        for cat in category_breakdown['expense']:
            prev_amount = prev_category_map.get(cat['category'], 0)
            change = 0
            if prev_amount > 0:
                change = round(((cat['amount'] - prev_amount) / prev_amount) * 100, 1)
            category_changes.append({
                'category': cat['category'],
                'amount': cat['amount'],
                'percentage': round((cat['amount'] / sum(item['amount'] for item in category_breakdown['expense'])) * 100, 1) if category_breakdown['expense'] else 0,
                'change': change
            })
    
    # Calculate top spending areas
    top_categories = sorted(category_changes, key=lambda x: x['amount'], reverse=True)[:3]
    top_percentage = sum(cat['percentage'] for cat in top_categories) if top_categories else 0
    
    return render_template('analytics/index.html',
                         summary=summary,
                         monthly_trends=monthly_trends,
                         category_breakdown=category_breakdown,
                         period_comparison=period_comparison,
                         insights=insights,
                         savings_rate=savings_rate,
                         category_changes=category_changes,
                         top_categories=top_categories,
                         top_percentage=top_percentage,
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