import pandas as pd
from datetime import datetime, date
from app import db
from app.models import Transaction, Category, Goal, CategoryRule

class FinanceAnalytics:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self._df: pd.DataFrame | None = None
        self._categories: dict[int, str] | None = None
    
    def load_transactions(self, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        query = Transaction.query.filter_by(user_id=self.user_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        transactions = query.order_by(Transaction.date).all()
        
        if not transactions:
            return pd.DataFrame(columns=['id', 'type', 'category', 'amount', 'description', 'date', 'category_id'])
        
        data = []
        for t in transactions:
            data.append({
                'id': t.id,
                'type': t.type,
                'category': t.category.name if t.category else 'Uncategorized',
                'category_id': t.category_id,
                'amount': float(t.amount),
                'description': t.description,
                'date': t.date
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        df['year'] = df['date'].dt.year
        df['month_num'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_month'] = df['date'].dt.day.apply(lambda d: (d - 1) // 7 + 1)
        
        return df
    
    def _get_categories(self) -> dict[int, str]:
        if self._categories is None:
            self._categories = {c.id: c.name for c in Category.query.filter_by(user_id=self.user_id).all()}
        return self._categories
    
    def get_summary(self, start_date: date | None = None, end_date: date | None = None) -> dict[str, float | int]:
        df = self.load_transactions(start_date, end_date)
        
        if df.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'net_savings': 0,
                'transaction_count': 0,
                'income_count': 0,
                'expense_count': 0
            }
        
        income = df[df['type'] == 'income']['amount'].sum()
        expenses = df[df['type'] == 'expense']['amount'].sum()
        
        return {
            'total_income': round(income, 2),
            'total_expenses': round(expenses, 2),
            'net_savings': round(income - expenses, 2),
            'transaction_count': len(df),
            'income_count': len(df[df['type'] == 'income']),
            'expense_count': len(df[df['type'] == 'expense'])
        }
    
    def get_monthly_trends(self, months: int = 12) -> list[dict[str, float | str]]:
        df = self.load_transactions()
        
        if df.empty:
            return []
        
        end_month = pd.Period(datetime.now().date(), freq='M')
        start_month = end_month - months + 1
        
        monthly = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        monthly.index = monthly.index.astype(str)
        
        result = []
        for i in range(months):
            period = start_month + i
            period_str = str(period)
            if period_str in monthly.index:
                income = monthly.loc[period_str].get('income', 0)
                expense = monthly.loc[period_str].get('expense', 0)
            else:
                income = 0
                expense = 0
            
            result.append({
                'month': period_str,
                'income': round(income, 2),
                'expenses': round(expense, 2),
                'net': round(income - expense, 2)
            })
        
        return result
    
    def get_category_breakdown(self, start_date: date | None = None, end_date: date | None = None, type_filter: str | None = None) -> dict[str, list[dict[str, float | str]]]:
        df = self.load_transactions(start_date, end_date)
        
        if df.empty:
            return {'income': [], 'expense': []}
        
        result = {'income': [], 'expense': []}
        
        for t in ['income', 'expense']:
            if type_filter and t != type_filter:
                continue
            cat_data = df[df['type'] == t].groupby('category')['amount'].sum().sort_values(ascending=False)
            for cat, amt in cat_data.items():
                result[t].append({'category': cat, 'amount': round(amt, 2)})
        
        return result
    
    def get_saving_opportunities(self, start_date: date | None = None, end_date: date | None = None) -> list[dict[str, float | str]]:
        df = self.load_transactions(start_date, end_date)
        
        if df.empty:
            return []
        
        opportunities = []
        expense_df = df[df['type'] == 'expense']
        
        if expense_df.empty:
            return opportunities
        
        category_totals = expense_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        total_expenses = expense_df['amount'].sum()
        
        for cat, amt in category_totals.items():
            percentage = (amt / total_expenses) * 100 if total_expenses > 0 else 0
            if percentage > 15:
                opportunities.append({
                    'category': cat,
                    'amount': round(amt, 2),
                    'percentage': round(percentage, 1),
                    'suggestion': self._get_suggestion(cat, amt, total_expenses)
                })
        
        monthly_expenses = expense_df.groupby('month')['amount'].sum()
        if len(monthly_expenses) >= 3:
            avg_monthly = monthly_expenses.mean()
            latest_expense = monthly_expenses.iloc[-1]
            
            if latest_expense > avg_monthly * 1.2:
                opportunities.append({
                    'category': 'Overall Spending',
                    'amount': round(latest_expense, 2),
                    'percentage': round((latest_expense / avg_monthly - 1) * 100, 1),
                    'suggestion': f'This month spending is {round((latest_expense / avg_monthly - 1) * 100, 1)}% above your {len(monthly_expenses)}-month average. Review recent transactions for non-essential purchases.'
                })
        
        return opportunities[:5]
    
    def _get_suggestion(self, category: str, amount: float, total: float) -> str:
        suggestions = {
            'Food': 'Consider meal planning and cooking at home more often',
            'Entertainment': 'Look for free or low-cost entertainment alternatives',
            'Shopping': 'Implement a 24-hour rule before non-essential purchases',
            'Transportation': 'Consider carpooling, public transit, or combining trips',
            'Utilities': 'Check for energy-saving opportunities and better rates',
            'Housing': 'Review if housing costs align with the 30% of income guideline',
            'Healthcare': 'Use preventive care and generic medications when possible',
            'Education': 'Look for free online resources and employer benefits',
            'Subscriptions': 'Audit recurring subscriptions and cancel unused ones',
        }
        return suggestions.get(category, f'Review {category} expenses for potential savings')
    
    def get_category_trends(self, months: int = 6) -> dict[str, dict[str, float]]:
        df = self.load_transactions()
        
        if df.empty:
            return {}
        
        expense_df = df[df['type'] == 'expense']
        if expense_df.empty:
            return {}
        
        end_month = pd.Period(datetime.now().date(), freq='M')
        start_month = end_month - months + 1
        
        trends = expense_df[expense_df['month'] >= start_month].groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)
        trends.index = trends.index.astype(str)
        
        return trends.round(2).to_dict('index')
    
    def get_spending_patterns(self, start_date: date | None = None, end_date: date | None = None) -> dict[str, dict[str, float] | float | int]:
        df = self.load_transactions(start_date, end_date)
        
        if df.empty:
            return {}
        
        expense_df = df[df['type'] == 'expense']
        if expense_df.empty:
            return {}
        
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        dow_data = expense_df.groupby('day_of_week')['amount'].mean()
        dow_data.index = [day_names[i] for i in dow_data.index]
        
        patterns = {
            'by_day_of_week': dow_data.round(2).to_dict(),
            'by_week_of_month': expense_df.groupby('week_of_month')['amount'].mean().round(2).to_dict(),
            'top_categories': expense_df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5).round(2).to_dict(),
            'avg_transaction': round(expense_df['amount'].mean(), 2),
            'median_transaction': round(expense_df['amount'].median(), 2),
            'transaction_count': len(expense_df),
        }
        
        return patterns
    
    def get_savings_rate(self, start_date: date | None = None, end_date: date | None = None) -> float:
        summary = self.get_summary(start_date, end_date)
        if summary['total_income'] == 0:
            return 0
        return round((summary['net_savings'] / summary['total_income']) * 100, 1)
    
    def get_projections(self) -> dict[str, float]:
        monthly = self.get_monthly_trends(6)
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
    
    def get_goal_progress(self, goal: Goal) -> dict[str, float | int | bool]:
        df = self.load_transactions(goal.start_date, goal.target_date)
        
        if df.empty:
            return {
                'saved': 0,
                'target': float(goal.target_amount),
                'percentage': 0,
                'months_elapsed': 0,
                'months_remaining': 0,
                'required_monthly': 0,
                'actual_monthly': 0,
                'on_track': False,
                'shortfall': float(goal.target_amount)
            }
        
        income = df[df['type'] == 'income']['amount'].sum()
        expenses = df[df['type'] == 'expense']['amount'].sum()
        saved = income - expenses
        
        total_months = (goal.target_date.year - goal.start_date.year) * 12 + (goal.target_date.month - goal.start_date.month) + 1
        today = date.today()
        if today > goal.target_date:
            months_elapsed = total_months
            months_remaining = 0
        elif today < goal.start_date:
            months_elapsed = 0
            months_remaining = total_months
        else:
            months_elapsed = (today.year - goal.start_date.year) * 12 + (today.month - goal.start_date.month) + 1
            months_remaining = max(0, total_months - months_elapsed)
        
        required_monthly = float(goal.target_amount) / total_months if total_months > 0 else 0
        actual_monthly = saved / months_elapsed if months_elapsed > 0 else 0
        projected_total = actual_monthly * total_months
        on_track = projected_total >= float(goal.target_amount) * 0.9
        shortfall = max(0, float(goal.target_amount) - projected_total)
        
        return {
            'saved': round(saved, 2),
            'target': float(goal.target_amount),
            'percentage': round((saved / float(goal.target_amount)) * 100, 1) if goal.target_amount > 0 else 0,
            'months_elapsed': months_elapsed,
            'months_remaining': months_remaining,
            'required_monthly': round(required_monthly, 2),
            'actual_monthly': round(actual_monthly, 2),
            'on_track': on_track,
            'shortfall': round(shortfall, 2)
        }
    
    def get_monthly_chart_data(self, months: int = 12) -> dict[str, list[str | float]]:
        monthly = self.get_monthly_trends(months)
        return {
            'labels': [m['month'] for m in monthly],
            'income': [m['income'] for m in monthly],
            'expenses': [m['expenses'] for m in monthly],
            'net': [m['net'] for m in monthly]
        }
    
    def get_category_chart_data(self, start_date: date | None = None, end_date: date | None = None) -> dict[str, dict[str, list[str | float]]]:
        breakdown = self.get_category_breakdown(start_date, end_date)
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
    
    def auto_categorize(self, description: str, amount: float | None = None, type_filter: str | None = None) -> int | None:
        rules = CategoryRule.query.filter_by(user_id=self.user_id).all()
        description_lower = description.lower()
        
        for rule in rules:
            if rule.keyword.lower() in description_lower:
                category = Category.query.get(rule.category_id)
                if category:
                    return category.id
        
        return None
    
    def apply_rules_to_transactions(self, transaction_ids: list[int] | None = None) -> int:
        query = Transaction.query.filter_by(user_id=self.user_id)
        if transaction_ids:
            query = query.filter(Transaction.id.in_(transaction_ids))
        
        transactions = query.all()
        updated = 0
        
        for t in transactions:
            if t.category_id is None or t.category.name == 'Uncategorized':
                cat_id = self.auto_categorize(t.description)
                if cat_id:
                    t.category_id = cat_id
                    updated += 1
        
        if updated > 0:
            db.session.commit()
        
        return updated

def get_user_transactions_df(user_id: int, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
    analytics = FinanceAnalytics(user_id)
    return analytics.load_transactions(start_date, end_date)