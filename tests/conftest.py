import pytest
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Category, Transaction, CategoryRule, Goal


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        
        # Seed default categories for testing
        user = User(email='test@example.com')
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.flush()
        
        Category.seed_default_categories(user.id)
        CategoryRule.seed_default_rules(user.id)
        
        # Create a sample goal for testing
        from datetime import date, timedelta
        goal = Goal(
            user_id=user.id,
            name='Test Goal',
            target_amount=1000.00,
            start_date=date.today(),
            target_date=date.today() + timedelta(days=365)
        )
        db.session.add(goal)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client, app):
    """A test client with a logged-in user."""
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def sample_user(app):
    """Get the sample user for testing."""
    with app.app_context():
        return User.query.filter_by(email='test@example.com').first()


@pytest.fixture
def sample_transaction(logged_in_client, app, sample_user):
    """Create a sample transaction for testing."""
    with app.app_context():
        from datetime import date
        from app.models import Transaction
        
        transaction = Transaction(
            user_id=sample_user.id,
            type='expense',
            category_id=1,
            amount=50.00,
            date=date.today(),
            description='Test transaction',
            source='manual'
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
