"""Tests for analytics service."""
import pytest
from datetime import date, timedelta
from app.analytics.services import FinanceAnalytics


class TestFinanceAnalytics:
    """Tests for the FinanceAnalytics service."""
    
    def test_summary_with_no_transactions(self, app, sample_user):
        """Test summary returns zeros when no transactions exist."""
        with app.app_context():
            analytics = FinanceAnalytics(sample_user.id)
            summary = analytics.get_summary()
            
            assert summary['total_income'] == 0
            assert summary['total_expenses'] == 0
            assert summary['net_savings'] == 0
            assert summary['transaction_count'] == 0
    
    def test_summary_with_transactions(self, app, sample_user):
        """Test summary calculates correctly with transactions."""
        from app import db
        
        with app.app_context():
            from app.models import Transaction
            
            today = date.today()
            
            # Add an income transaction
            income = Transaction(
                user_id=sample_user.id,
                type='income',
                category_id=1,
                amount=2000.00,
                date=today,
                description='Salary',
                source='manual',
                dedup_hash=Transaction.compute_dedup_hash(
                    sample_user.id, today, 2000.00, 'Salary'
                )
            )
            db.session.add(income)
            db.session.commit()
            
            analytics = FinanceAnalytics(sample_user.id)
            summary = analytics.get_summary()
            
            assert summary['total_income'] == 2000.00
            # Net savings = income - expenses (expense from fixture = 50)
            assert summary['net_savings'] == 2000.00 - 50.00  # 1950.00
    
    def test_monthly_trends_empty(self, app, sample_user):
        """Test monthly trends returns empty list when no transactions."""
        with app.app_context():
            analytics = FinanceAnalytics(sample_user.id)
            trends = analytics.get_monthly_trends(6)
            
            assert trends == []
    
    def test_category_breakdown_empty(self, app, sample_user):
        """Test category breakdown returns empty when no transactions."""
        with app.app_context():
            analytics = FinanceAnalytics(sample_user.id)
            breakdown = analytics.get_category_breakdown()
            
            assert breakdown['income'] == []
            assert breakdown['expense'] == []
    
    def test_savings_rate_zero_when_no_income(self, app, sample_user):
        """Test savings rate returns 0 when there's no income."""
        with app.app_context():
            analytics = FinanceAnalytics(sample_user.id)
            rate = analytics.get_savings_rate()
            
            assert rate == 0
    
    def test_auto_categorize_finds_matching_rule(self, app, sample_user):
        """Test auto-categorize finds matching rules."""
        with app.app_context():
            from app.models import Category
            
            # Get the Food category
            food_category = Category.query.filter_by(
                user_id=sample_user.id, 
                name='Food'
            ).first()
            
            analytics = FinanceAnalytics(sample_user.id)
            category_id = analytics.auto_categorize('Grocery store purchase')
            
            # Should match the 'grocery' rule for Food category
            assert category_id == food_category.id
    
    def test_auto_categorize_returns_none_for_no_match(self, app, sample_user):
        """Test auto-categorize returns None when no rules match."""
        with app.app_context():
            analytics = FinanceAnalytics(sample_user.id)
            category_id = analytics.auto_categorize('random unknown transaction')
            
            assert category_id is None


class TestGoalProgress:
    """Tests for goal progress calculation."""
    
    def test_goal_progress_with_no_transactions(self, app, sample_user):
        """Test goal progress returns zeros when no transactions in period."""
        from app import db
        from app.models import Goal
        
        with app.app_context():
            start_date = date.today()
            target_date = date.today() + timedelta(days=365)
            
            goal = Goal(
                user_id=sample_user.id,
                name='Test Goal',
                target_amount=1000.00,
                start_date=start_date,
                target_date=target_date
            )
            db.session.add(goal)
            db.session.commit()
            
            analytics = FinanceAnalytics(sample_user.id)
            progress = analytics.get_goal_progress(goal)
            
            assert progress['saved'] == 0
            assert progress['percentage'] == 0
            assert progress['on_track'] is False
    
    def test_goal_progress_calculation(self, app, sample_user):
        """Test goal progress calculates correctly."""
        from app import db
        from app.models import Goal, Transaction
        
        with app.app_context():
            start_date = date.today().replace(day=1)
            target_date = date.today().replace(day=28) + timedelta(days=30)
            
            goal = Goal(
                user_id=sample_user.id,
                name='Test Goal',
                target_amount=1000.00,
                start_date=start_date,
                target_date=target_date
            )
            db.session.add(goal)
            db.session.commit()
            
            # Add some income and expenses in the goal period
            income = Transaction(
                user_id=sample_user.id,
                type='income',
                category_id=1,
                amount=500.00,
                date=start_date,
                description='Income',
                source='manual'
            )
            expense = Transaction(
                user_id=sample_user.id,
                type='expense',
                category_id=2,
                amount=100.00,
                date=start_date,
                description='Expense',
                source='manual'
            )
            db.session.add_all([income, expense])
            db.session.commit()
            
            analytics = FinanceAnalytics(sample_user.id)
            progress = analytics.get_goal_progress(goal)
            
            # Saved should be income - expenses = 400
            assert progress['saved'] == 400.00
            # Percentage should be 400/1000 = 40%
            assert progress['percentage'] == 40.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
