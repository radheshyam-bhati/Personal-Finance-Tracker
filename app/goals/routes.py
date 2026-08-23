from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.goals import goals_bp
from app import db
from app.models import Goal, AuditLog
from app.forms import GoalForm
from app.analytics.services import FinanceAnalytics

@goals_bp.route('/')
@login_required
def index():
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.target_date).all()
    
    analytics = FinanceAnalytics(current_user.id)
    goals_progress = [analytics.get_goal_progress(g) for g in goals]
    
    return render_template('goals/index.html', goals=list(zip(goals, goals_progress)))

@goals_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = GoalForm()
    
    if form.validate_on_submit():
        goal = Goal(
            user_id=current_user.id,
            name=form.name.data,
            target_amount=form.target_amount.data,
            start_date=form.start_date.data,
            target_date=form.target_date.data
        )
        
        db.session.add(goal)
        db.session.flush()
        
        audit = AuditLog(
            user_id=current_user.id,
            entity_type='goal',
            entity_id=goal.id,
            action='create',
            previous_value=None
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Savings goal created successfully!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goals/form.html', form=form, title='Create Savings Goal')

@goals_bp.route('/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    form = GoalForm(obj=goal)
    
    if form.validate_on_submit():
        previous = {
            'name': goal.name,
            'target_amount': str(goal.target_amount),
            'start_date': str(goal.start_date),
            'target_date': str(goal.target_date)
        }
        
        goal.name = form.name.data
        goal.target_amount = form.target_amount.data
        goal.start_date = form.start_date.data
        goal.target_date = form.target_date.data
        
        audit = AuditLog(
            user_id=current_user.id,
            entity_type='goal',
            entity_id=goal.id,
            action='update',
            previous_value=str(previous)
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Goal updated successfully!', 'success')
        return redirect(url_for('goals.index'))
    
    return render_template('goals/form.html', form=form, title='Edit Savings Goal', goal=goal)

@goals_bp.route('/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    previous = {
        'name': goal.name,
        'target_amount': str(goal.target_amount),
        'start_date': str(goal.start_date),
        'target_date': str(goal.target_date)
    }
    
    audit = AuditLog(
        user_id=current_user.id,
        entity_type='goal',
        entity_id=goal.id,
        action='delete',
        previous_value=str(previous)
    )
    db.session.add(audit)
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals.index'))

@goals_bp.route('/<int:goal_id>')
@login_required
def detail(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    
    analytics = FinanceAnalytics(current_user.id)
    progress = analytics.get_goal_progress(goal)
    
    from app import db
    from app.models import Transaction
    from datetime import date
    
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= goal.start_date,
        Transaction.date <= goal.target_date
    ).order_by(Transaction.date.desc()).limit(50).all()
    
    return render_template('goals/detail.html', goal=goal, progress=progress, transactions=transactions)