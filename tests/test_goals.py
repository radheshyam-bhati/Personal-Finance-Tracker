"""Tests for goal routes and models."""
import pytest
from datetime import date, timedelta


class TestGoalsIndex:
    """Tests for the goals index route."""
    
    def test_goals_page_loads(self, logged_in_client):
        """Test that the goals page loads."""
        response = logged_in_client.get('/goals')
        assert response.status_code == 200
        assert b'Savings Goals' in response.data
    
    def test_goals_page_shows_empty_state(self, logged_in_client):
        """Test that empty state shows when no goals exist."""
        response = logged_in_client.get('/goals')
        assert response.status_code == 200
        assert b'Create Goal' in response.data


class TestGoalCreate:
    """Tests for creating goals."""
    
    def test_create_goal_page_loads(self, logged_in_client):
        """Test that the create goal page loads."""
        response = logged_in_client.get('/goals/create')
        assert response.status_code == 200
        assert b'Create Savings Goal' in response.data
    
    def test_create_goal_requires_login(self, client):
        """Test that creating goals requires authentication."""
        response = client.get('/goals/create', follow_redirects=False)
        assert response.status_code == 302
    
    def test_create_goal_validates_dates(self, logged_in_client):
        """Test that goal form validates date constraints."""
        future_date = date.today() + timedelta(days=30)
        response = logged_in_client.post('/goals/create', data={
            'name': 'Test Goal',
            'target_amount': 1000.00,
            'start_date': future_date,
            'target_date': date.today()  # Target before start should fail
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Target date must be after start date' in response.data


class TestGoalModel:
    """Tests for the Goal model."""
    
    def test_goal_creation(self, app, sample_user):
        """Test creating a goal."""
        with app.app_context():
            from app.models import Goal
            
            start_date = date.today()
            target_date = date.today() + timedelta(days=365)
            
            goal = Goal(
                user_id=sample_user.id,
                name='Emergency Fund',
                target_amount=10000.00,
                start_date=start_date,
                target_date=target_date
            )
            db.session.add(goal)
            db.session.commit()
            
            # Verify goal was created
            saved = Goal.query.get(goal.id)
            assert saved is not None
            assert saved.name == 'Emergency Fund'
            assert float(saved.target_amount) == 10000.00
    
    def test_goal_target_after_start_constraint(self, app, sample_user):
        """Test that goal target_date must be after start_date."""
        with app.app_context():
            from app.models import Goal
            
            start_date = date.today()
            target_date = date.today() + timedelta(days=30)
            
            goal = Goal(
                user_id=sample_user.id,
                name='Test Goal',
                target_amount=1000.00,
                start_date=start_date,
                target_date=target_date
            )
            db.session.add(goal)
            db.session.commit()
            
            assert Goal.query.count() == 1


class TestGoalDetail:
    """Tests for goal detail view."""
    
    def test_goal_detail_page_loads(self, app, logged_in_client, sample_user):
        """Test that goal detail page loads."""
        with app.app_context():
            from app.models import Goal
            
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
            
            response = logged_in_client.get(f'/goals/{goal.id}')
            assert response.status_code == 200
            assert b'Test Goal' in response.data
    
    def test_goal_detail_requires_login(self, client, app, sample_user):
        """Test that goal detail requires authentication."""
        with app.app_context():
            from app.models import Goal
            
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
            
            response = client.get(f'/goals/{goal.id}', follow_redirects=False)
            assert response.status_code == 302


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
