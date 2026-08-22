import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from analytics import FinanceAnalytics

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

DATA_FILE = 'transactions.json'

def load_transactions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_transactions(transactions):
    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f, indent=2, default=str)

@app.route('/')
def index():
    transactions = load_transactions()
    analytics = FinanceAnalytics(transactions)
    
    summary = analytics.get_summary()
    monthly_trends = analytics.get_monthly_trends()
    category_breakdown = analytics.get_category_breakdown()
    saving_opportunities = analytics.get_saving_opportunities()
    
    recent_transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)[:10]
    
    return render_template('dashboard.html',
                         summary=summary,
                         monthly_trends=monthly_trends,
                         category_breakdown=category_breakdown,
                         saving_opportunities=saving_opportunities,
                         recent_transactions=recent_transactions)

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        transaction = {
            'id': datetime.now().timestamp(),
            'type': request.form['type'],
            'category': request.form['category'],
            'amount': float(request.form['amount']),
            'description': request.form['description'],
            'date': request.form['date']
        }
        
        transactions = load_transactions()
        transactions.append(transaction)
        save_transactions(transactions)
        
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('index'))
    
    categories = {
        'income': ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other Income'],
        'expense': ['Housing', 'Food', 'Transportation', 'Utilities', 'Entertainment', 'Healthcare', 'Shopping', 'Education', 'Other Expense']
    }
    return render_template('add_transaction.html', categories=categories, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/transactions')
def view_transactions():
    transactions = load_transactions()
    transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)
    
    filter_type = request.args.get('type')
    filter_category = request.args.get('category')
    filter_month = request.args.get('month')
    
    if filter_type:
        transactions = [t for t in transactions if t['type'] == filter_type]
    if filter_category:
        transactions = [t for t in transactions if t['category'] == filter_category]
    if filter_month:
        transactions = [t for t in transactions if t['date'].startswith(filter_month)]
    
    categories = set(t['category'] for t in transactions)
    months = sorted(set(t['date'][:7] for t in transactions), reverse=True)
    
    return render_template('transactions.html',
                         transactions=transactions,
                         categories=categories,
                         months=months,
                         filters={'type': filter_type, 'category': filter_category, 'month': filter_month})

@app.route('/delete/<float:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transactions = load_transactions()
    transactions = [t for t in transactions if t['id'] != transaction_id]
    save_transactions(transactions)
    flash('Transaction deleted!', 'success')
    return redirect(url_for('view_transactions'))

@app.route('/analytics')
def analytics():
    transactions = load_transactions()
    analytics = FinanceAnalytics(transactions)
    
    monthly_trends = analytics.get_monthly_trends()
    category_trends = analytics.get_category_trends()
    spending_patterns = analytics.get_spending_patterns()
    savings_rate = analytics.get_savings_rate()
    projections = analytics.get_projections()
    
    return render_template('analytics.html',
                         monthly_trends=monthly_trends,
                         category_trends=category_trends,
                         spending_patterns=spending_patterns,
                         savings_rate=savings_rate,
                         projections=projections)

@app.route('/api/chart-data')
def chart_data():
    transactions = load_transactions()
    analytics = FinanceAnalytics(transactions)
    
    monthly_data = analytics.get_monthly_chart_data()
    category_data = analytics.get_category_chart_data()
    
    return jsonify({
        'monthly': monthly_data,
        'category': category_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)