import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

class FinanceAnalytics:
    def __init__(self, transactions):
        self.transactions = transactions
        self.df = self._to_dataframe()
    
    def _to_dataframe(self):
        if not self.transactions:
            return pd.DataFrame(columns=['id', 'type', 'category', 'amount', 'description', 'date'])
        
        df = pd.DataFrame(self.transactions)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        df['amount'] = pd.to_numeric(df['amount'])
        return df
    
    def get_summary(self):
        if self.df.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'net_savings': 0,
                'transaction_count': 0
            }
        
        income = self.df[self.df['type'] == 'income']['amount'].sum()
        expenses = self.df[self.df['type'] == 'expense']['amount'].sum()
        
        return {
            'total_income': round(income, 2),
            'total_expenses': round(expenses, 2),
            'net_savings': round(income - expenses, 2),
            'transaction_count': len(self.df)
        }
    
    def get_monthly_trends(self):
        if self.df.empty:
            return []
        
        monthly = self.df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        monthly.index = monthly.index.astype(str)
        
        result = []
        for month in monthly.index:
            income = monthly.loc[month].get('income', 0)
            expense = monthly.loc[month].get('expense', 0)
            result.append({
                'month': month,
                'income': round(income, 2),
                'expenses': round(expense, 2),
                'net': round(income - expense, 2)
            })
        return result
    
    def get_category_breakdown(self):
        if self.df.empty:
            return {'income': [], 'expense': []}
        
        result = {'income': [], 'expense': []}
        
        for t in ['income', 'expense']:
            cat_data = self.df[self.df['type'] == t].groupby('category')['amount'].sum().sort_values(ascending=False)
            for cat, amt in cat_data.items():
                result[t].append({'category': cat, 'amount': round(amt, 2)})
        
        return result
    
    def get_saving_opportunities(self):
        if self.df.empty:
            return []
        
        opportunities = []
        expense_df = self.df[self.df['type'] == 'expense']
        
        if expense_df.empty:
            return opportunities
        
        category_totals = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        total_expenses = expense_df['amount'].sum()
        
        for cat, amt in category_totals.items():
            percentage = (amt / total_expenses) * 100
            if percentage > 15:
                opportunities.append({
                    'category': cat,
                    'amount': round(amt, 2),
                    'percentage': round(percentage, 1),
                    'suggestion': self._get_suggestion(cat, amt)
                })
        
        monthly_expenses = expense_df.groupby('month')['amount'].sum()
        if len(monthly_expenses) >= 3:
            avg_monthly = monthly_expenses.mean()
            latest_month = monthly_expenses.index[-1]
            latest_expense = monthly_expenses.iloc[-1]
            
            if latest_expense > avg_monthly * 1.2:
                opportunities.append({
                    'category': 'Overall Spending',
                    'amount': round(latest_expense, 2),
                    'percentage': round((latest_expense / avg_monthly - 1) * 100, 1),
                    'suggestion': f'This month spending is {round((latest_expense / avg_monthly - 1) * 100, 1)}% above average. Review recent transactions for non-essential purchases.'
                })
        
        return opportunities[:5]
    
    def _get_suggestion(self, category, amount):
        suggestions = {
            'Food': 'Consider meal planning and cooking at home more often',
            'Entertainment': 'Look for free/low-cost entertainment alternatives',
            'Shopping': 'Implement a 24-hour rule before non-essential purchases',
            'Transportation': 'Consider carpooling, public transit, or combining trips',
            'Utilities': 'Check for energy-saving opportunities and better rates',
            'Housing': 'Review if housing costs align with the 30% income guideline',
            'Healthcare': 'Use preventive care and generic medications when possible',
            'Education': 'Look for free online resources and employer benefits',
        }
        return suggestions.get(category, f'Review {category} expenses for potential savings')
    
    def get_category_trends(self):
        if self.df.empty:
            return {}
        
        expense_df = self.df[self.df['type'] == 'expense']
        if expense_df.empty:
            return {}
        
        trends = expense_df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)
        trends.index = trends.index.astype(str)
        return trends.round(2).to_dict('index')
    
    def get_spending_patterns(self):
        if self.df.empty:
            return {}
        
        expense_df = self.df[self.df['type'] == 'expense']
        if expense_df.empty:
            return {}
        
        patterns = {
            'by_day_of_week': expense_df.groupby(expense_df['date'].dt.dayofweek)['amount'].mean().round(2).to_dict(),
            'by_week_of_month': expense_df.groupby(expense_df['date'].dt.day.apply(lambda d: (d-1)//7 + 1))['amount'].mean().round(2).to_dict(),
            'top_categories': expense_df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5).round(2).to_dict(),
            'avg_transaction': round(expense_df['amount'].mean(), 2),
            'median_transaction': round(expense_df['amount'].median(), 2),
        }
        
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        patterns['by_day_of_week'] = {day_names[k]: v for k, v in patterns['by_day_of_week'].items()}
        
        return patterns
    
    def get_savings_rate(self):
        summary = self.get_summary()
        if summary['total_income'] == 0:
            return 0
        return round((summary['net_savings'] / summary['total_income']) * 100, 1)
    
    def get_projections(self):
        if self.df.empty:
            return {}
        
        monthly = self.get_monthly_trends()
        if len(monthly) < 2:
            return {}
        
        recent_months = monthly[-3:]
        avg_income = sum(m['income'] for m in recent_months) / len(recent_months)
        avg_expenses = sum(m['expenses'] for m in recent_months) / len(recent_months)
        avg_net = sum(m['net'] for m in recent_months) / len(recent_months)
        
        return {
            'next_month_income': round(avg_income, 2),
            'next_month_expenses': round(avg_expenses, 2),
            'next_month_net': round(avg_net, 2),
            'projected_annual_savings': round(avg_net * 12, 2)
        }
    
    def get_monthly_chart_data(self):
        monthly = self.get_monthly_trends()
        return {
            'labels': [m['month'] for m in monthly],
            'income': [m['income'] for m in monthly],
            'expenses': [m['expenses'] for m in monthly],
            'net': [m['net'] for m in monthly]
        }
    
    def get_category_chart_data(self):
        breakdown = self.get_category_breakdown()
        return {
            'income': {
                'labels': [c['category'] for c in breakdown['income']],
                'data': [c['amount'] for c in breakdown['income']]
            },
            'expense': {
                'labels': [c['category'] for c in breakdown['expense']],
                'data': [c['amount'] for c in breakdown['expense']]
            }
        }