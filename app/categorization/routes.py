from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.categorization import categorization_bp
from app import db
from app.models import Category, CategoryRule, Transaction
from app.forms import CategoryForm, CategoryRuleForm
from app.analytics.services import FinanceAnalytics

@categorization_bp.route('/')
@login_required
def index():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    # Get uncategorized transaction count
    uncategorized_count = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        (Transaction.category_id.is_(None)) | (Transaction.category.has(Category.name == 'Uncategorized'))
    ).count()
    
    # Get category spending data
    analytics = FinanceAnalytics(current_user.id)
    category_breakdown = analytics.get_category_breakdown(type_filter='expense')
    
    # Build category spending map
    category_spending = {}
    total_expenses = sum(item['amount'] for item in category_breakdown['expense'])
    
    for item in category_breakdown['expense']:
        category_spending[item['category']] = {
            'amount': item['amount'],
            'percentage': round((item['amount'] / total_expenses * 100), 1) if total_expenses > 0 else 0
        }
    
    # Get automation rules
    rules = CategoryRule.query.filter_by(user_id=current_user.id).join(Category).order_by(Category.name, CategoryRule.keyword).limit(10).all()
    
    return render_template('categorization/index.html', 
                         categories=categories, 
                         uncategorized_count=uncategorized_count,
                         category_spending=category_spending,
                         total_expenses=total_expenses,
                         rules=rules)

@categorization_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        existing = Category.query.filter_by(user_id=current_user.id, name=form.name.data).first()
        if existing:
            flash('A category with this name already exists.', 'danger')
            return render_template('categorization/category_form.html', form=form, title='Create Category')
        
        category = Category(user_id=current_user.id, name=form.name.data, is_default=False)
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('categorization.index'))
    
    return render_template('categorization/category_form.html', form=form, title='Create Category')

@categorization_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    if category.is_default:
        flash('Default categories cannot be renamed.', 'warning')
        return redirect(url_for('categorization.index'))
    
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        existing = Category.query.filter(
            Category.user_id == current_user.id,
            Category.name == form.name.data,
            Category.id != category_id
        ).first()
        if existing:
            flash('A category with this name already exists.', 'danger')
            return render_template('categorization/category_form.html', form=form, title='Edit Category')
        
        category.name = form.name.data
        db.session.commit()
        
        flash('Category updated successfully!', 'success')
        return redirect(url_for('categorization.index'))
    
    return render_template('categorization/category_form.html', form=form, title='Edit Category')

@categorization_bp.route('/rules')
@login_required
def rules():
    rules = CategoryRule.query.filter_by(user_id=current_user.id).join(Category).order_by(Category.name, CategoryRule.keyword).all()
    return render_template('categorization/rules.html', rules=rules)

@categorization_bp.route('/rules/create', methods=['GET', 'POST'])
@login_required
def create_rule():
    form = CategoryRuleForm(user_id=current_user.id)
    
    if form.validate_on_submit():
        rule = CategoryRule(
            user_id=current_user.id,
            category_id=form.category.data,
            keyword=form.keyword.data.lower().strip()
        )
        db.session.add(rule)
        db.session.commit()
        
        flash('Categorization rule created successfully!', 'success')
        return redirect(url_for('categorization.rules'))
    
    return render_template('categorization/rule_form.html', form=form, title='Create Rule')

@categorization_bp.route('/rules/<int:rule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rule(rule_id):
    rule = CategoryRule.query.filter_by(id=rule_id, user_id=current_user.id).first_or_404()
    
    form = CategoryRuleForm(user_id=current_user.id, obj=rule)
    
    if form.validate_on_submit():
        rule.keyword = form.keyword.data.lower().strip()
        rule.category_id = form.category.data
        db.session.commit()
        
        flash('Rule updated successfully!', 'success')
        return redirect(url_for('categorization.rules'))
    
    return render_template('categorization/rule_form.html', form=form, title='Edit Rule')

@categorization_bp.route('/rules/<int:rule_id>/delete', methods=['POST'])
@login_required
def delete_rule(rule_id):
    rule = CategoryRule.query.filter_by(id=rule_id, user_id=current_user.id).first_or_404()
    db.session.delete(rule)
    db.session.commit()
    
    flash('Rule deleted successfully!', 'success')
    return redirect(url_for('categorization.rules'))

@categorization_bp.route('/review')
@login_required
def review():
    uncategorized = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        (Transaction.category_id.is_(None)) | (Transaction.category.has(Category.name == 'Uncategorized'))
    ).order_by(Transaction.date.desc()).limit(100).all()
    
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    return render_template('categorization/review.html', transactions=uncategorized, categories=categories)

@categorization_bp.route('/review/<int:transaction_id>', methods=['POST'])
@login_required
def categorize_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    category_id = request.form.get('category_id', type=int)
    if category_id:
        category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
        if category:
            transaction.category_id = category_id
            db.session.commit()
            
            analytics = FinanceAnalytics(current_user.id)
            analytics.apply_rules_to_transactions([transaction_id])
            
            flash('Transaction categorized!', 'success')
        else:
            flash('Invalid category.', 'danger')
    else:
        flash('No category selected.', 'danger')
    
    return redirect(url_for('categorization.review'))

@categorization_bp.route('/auto-categorize', methods=['POST'])
@login_required
def auto_categorize():
    analytics = FinanceAnalytics(current_user.id)
    updated = analytics.apply_rules_to_transactions()
    
    flash(f'Auto-categorized {updated} transactions.', 'success')
    return redirect(url_for('categorization.review'))