import pandas as pd
import io
import csv
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.transactions import transactions_bp
from app import db
from app.models import Transaction, Category, ImportBatch, AuditLog
from app.forms import TransactionForm, ImportForm, TransactionFilterForm
from app.analytics.services import FinanceAnalytics

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_csv(file_stream, user_id):
    try:
        df = pd.read_csv(file_stream)
    except Exception as e:
        return None, [f"Failed to parse CSV: {str(e)}"]
    
    required_columns = ['date', 'description', 'amount']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return None, [f"Missing required columns: {', '.join(missing)}"]
    
    df.columns = [c.lower().strip() for c in df.columns]
    
    transactions = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            date_val = pd.to_datetime(row['date']).date()
        except:
            errors.append(f"Row {idx + 2}: Invalid date format '{row['date']}'")
            continue
        
        description = str(row['description']).strip() if pd.notna(row['description']) else ''
        if not description:
            errors.append(f"Row {idx + 2}: Empty description")
            continue
        
        try:
            amount = float(row['amount'])
            if amount <= 0:
                errors.append(f"Row {idx + 2}: Amount must be positive")
                continue
        except:
            errors.append(f"Row {idx + 2}: Invalid amount '{row['amount']}'")
            continue
        
        t_type = 'expense'
        if 'type' in df.columns and pd.notna(row['type']):
            t_type = str(row['type']).strip().lower()
            if t_type not in ['income', 'expense']:
                t_type = 'expense'
        
        category_id = None
        if 'category' in df.columns and pd.notna(row['category']):
            cat_name = str(row['category']).strip()
            category = Category.query.filter_by(user_id=user_id, name=cat_name).first()
            if category:
                category_id = category.id
        
        transactions.append({
            'date': date_val,
            'description': description,
            'amount': amount,
            'type': t_type,
            'category_id': category_id
        })
    
    return transactions, errors

@transactions_bp.route('/')
@login_required
def index():
    form = TransactionFilterForm(user_id=current_user.id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if request.args.get('type'):
        query = query.filter(Transaction.type == request.args['type'])
        form.type.data = request.args['type']
    
    if request.args.get('category', type=int):
        query = query.filter(Transaction.category_id == request.args['category'])
        form.category.data = request.args['category']
    
    if request.args.get('start_date'):
        try:
            start = datetime.strptime(request.args['start_date'], '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start)
            form.start_date.data = start
        except:
            pass
    
    if request.args.get('end_date'):
        try:
            end = datetime.strptime(request.args['end_date'], '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end)
            form.end_date.data = end
        except:
            pass
    
    if request.args.get('min_amount', type=float):
        query = query.filter(Transaction.amount >= request.args['min_amount'])
        form.min_amount.data = request.args['min_amount']
    
    if request.args.get('max_amount', type=float):
        query = query.filter(Transaction.amount <= request.args['max_amount'])
        form.max_amount.data = request.args['max_amount']
    
    if request.args.get('search'):
        search = f"%{request.args['search']}%"
        query = query.filter(Transaction.description.ilike(search))
        form.search.data = request.args['search']
    
    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    transactions = pagination.items
    
    return render_template('transactions/index.html',
                         transactions=transactions,
                         pagination=pagination,
                         form=form)

@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = TransactionForm(user_id=current_user.id)
    
    if form.validate_on_submit():
        transaction = Transaction(
            user_id=current_user.id,
            type=form.type.data,
            category_id=form.category.data,
            amount=form.amount.data,
            date=form.date.data,
            description=form.description.data or '',
            source='manual',
            dedup_hash=Transaction.compute_dedup_hash(
                current_user.id, form.date.data, form.amount.data, form.description.data or ''
            )
        )
        
        existing = Transaction.query.filter_by(
            user_id=current_user.id,
            dedup_hash=transaction.dedup_hash
        ).first()
        
        if existing:
            flash('A transaction with the same date, amount, and description already exists.', 'warning')
            return render_template('transactions/form.html', form=form, title='Add Transaction')
        
        db.session.add(transaction)
        db.session.flush()
        
        audit = AuditLog(
            user_id=current_user.id,
            entity_type='transaction',
            entity_id=transaction.id,
            action='create',
            previous_value=None
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions.index'))
    
    return render_template('transactions/form.html', form=form, title='Add Transaction')

@transactions_bp.route('/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    form = TransactionForm(user_id=current_user.id, obj=transaction)
    
    if form.validate_on_submit():
        previous = {
            'type': transaction.type,
            'category_id': transaction.category_id,
            'amount': str(transaction.amount),
            'date': str(transaction.date),
            'description': transaction.description
        }
        
        transaction.type = form.type.data
        transaction.category_id = form.category.data
        transaction.amount = form.amount.data
        transaction.date = form.date.data
        transaction.description = form.description.data or ''
        transaction.dedup_hash = Transaction.compute_dedup_hash(
            current_user.id, form.date.data, form.amount.data, form.description.data or ''
        )
        
        audit = AuditLog(
            user_id=current_user.id,
            entity_type='transaction',
            entity_id=transaction.id,
            action='update',
            previous_value=str(previous)
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transactions.index'))
    
    return render_template('transactions/form.html', form=form, title='Edit Transaction', transaction=transaction)

@transactions_bp.route('/<int:transaction_id>/delete', methods=['POST'])
@login_required
def delete(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    previous = {
        'type': transaction.type,
        'category_id': transaction.category_id,
        'amount': str(transaction.amount),
        'date': str(transaction.date),
        'description': transaction.description
    }
    
    audit = AuditLog(
        user_id=current_user.id,
        entity_type='transaction',
        entity_id=transaction.id,
        action='delete',
        previous_value=str(previous)
    )
    db.session.add(audit)
    
    db.session.delete(transaction)
    db.session.commit()
    
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('transactions.index'))

@transactions_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    form = ImportForm()
    
    if form.validate_on_submit():
        file = form.csv_file.data
        if not allowed_file(file.filename):
            flash('Only CSV files are allowed.', 'danger')
            return render_template('transactions/import.html', form=form)
        
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        transactions_data, errors = parse_csv(stream, current_user.id)
        
        if transactions_data is None:
            for error in errors:
                flash(error, 'danger')
            return render_template('transactions/import.html', form=form)
        
        if not transactions_data:
            flash('No valid transactions found in the CSV.', 'warning')
            return render_template('transactions/import.html', form=form)
        
        import_batch = ImportBatch(
            user_id=current_user.id,
            filename=secure_filename(file.filename),
            row_count=len(transactions_data) + len(errors),
            rows_imported=0,
            rows_flagged=len(errors)
        )
        db.session.add(import_batch)
        db.session.flush()
        
        imported = 0
        duplicates = 0
        analytics = FinanceAnalytics(current_user.id)
        
        for t_data in transactions_data:
            t_data['user_id'] = current_user.id
            t_data['source'] = 'csv_import'
            t_data['import_batch_id'] = import_batch.id
            t_data['dedup_hash'] = Transaction.compute_dedup_hash(
                current_user.id, t_data['date'], t_data['amount'], t_data['description']
            )
            
            existing = Transaction.query.filter_by(
                user_id=current_user.id,
                dedup_hash=t_data['dedup_hash']
            ).first()
            
            if existing:
                duplicates += 1
                continue
            
            if t_data['category_id'] is None:
                cat_id = analytics.auto_categorize(t_data['description'])
                if cat_id:
                    t_data['category_id'] = cat_id
            
            transaction = Transaction(**t_data)
            db.session.add(transaction)
            imported += 1
        
        import_batch.rows_imported = imported
        db.session.commit()
        
        if errors:
            flash(f'Imported {imported} transactions. {len(errors)} rows had errors and were skipped.', 'warning')
            for error in errors[:5]:
                flash(error, 'warning')
        else:
            flash(f'Successfully imported {imported} transactions!', 'success')
        
        if duplicates:
            flash(f'{duplicates} duplicate transactions were skipped.', 'info')
        
        return redirect(url_for('transactions.index'))
    
    return render_template('transactions/import.html', form=form)

@transactions_bp.route('/import/batches')
@login_required
def import_batches():
    batches = ImportBatch.query.filter_by(user_id=current_user.id).order_by(ImportBatch.imported_at.desc()).all()
    return render_template('transactions/import_batches.html', batches=batches)

@transactions_bp.route('/import/batches/<int:batch_id>/undo', methods=['POST'])
@login_required
def undo_import(batch_id):
    batch = ImportBatch.query.filter_by(id=batch_id, user_id=current_user.id).first_or_404()
    
    transactions = Transaction.query.filter_by(import_batch_id=batch_id, user_id=current_user.id).all()
    
    for t in transactions:
        previous = {
            'type': t.type,
            'category_id': t.category_id,
            'amount': str(t.amount),
            'date': str(t.date),
            'description': t.description
        }
        audit = AuditLog(
            user_id=current_user.id,
            entity_type='transaction',
            entity_id=t.id,
            action='delete',
            previous_value=str(previous)
        )
        db.session.add(audit)
        db.session.delete(t)
    
    db.session.delete(batch)
    db.session.commit()
    
    flash(f'Import batch undone. {len(transactions)} transactions removed.', 'success')
    return redirect(url_for('transactions.import_batches'))