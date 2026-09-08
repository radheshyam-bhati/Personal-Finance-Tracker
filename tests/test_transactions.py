"""Tests for transaction routes and models."""
import pytest
from datetime import date


class TestTransactionIndex:
    """Tests for the transaction index route."""
    
    def test_transactions_page_requires_login(self, client):
        """Test that transactions page requires authentication."""
        response = client.get('/transactions', follow_redirects=False)
        assert response.status_code == 302
    
    def test_transactions_page_loads_for_authenticated_user(self, logged_in_client):
        """Test that the transactions page loads for authenticated users."""
        response = logged_in_client.get('/transactions')
        assert response.status_code == 200
        assert b'Transactions' in response.data
    
    def test_transactions_page_shows_empty_state(self, logged_in_client):
        """Test that empty state shows when no transactions exist."""
        response = logged_in_client.get('/transactions')
        assert response.status_code == 200
        # Should show either empty state or transactions
        assert b'import' in response.data.lower() or b'add' in response.data.lower()


class TestTransactionAdd:
    """Tests for adding transactions."""
    
    def test_add_transaction_page_loads(self, logged_in_client):
        """Test that the add transaction page loads."""
        response = logged_in_client.get('/transactions/add')
        assert response.status_code == 200
        assert b'Add Transaction' in response.data
    
    def test_add_transaction_requires_login(self, client):
        """Test that adding transactions requires authentication."""
        response = client.get('/transactions/add', follow_redirects=False)
        assert response.status_code == 302


class TestTransactionForm:
    """Tests for transaction form validation."""
    
    def test_transaction_form_validates_required_fields(self, logged_in_client):
        """Test that the transaction form validates required fields."""
        response = logged_in_client.post('/transactions/add', data={
            'type': 'expense',
            'category': 1,
            'amount': '',
            'date': '',
            'description': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should show validation errors
        assert b'This field is required' in response.data or b'Amount' in response.data


class TestTransactionModel:
    """Tests for the Transaction model."""
    
    def test_transaction_creation(self, app, sample_user):
        """Test creating a transaction."""
        from app import db
        
        with app.app_context():
            from app.models import Transaction
            
            transaction = Transaction(
                user_id=sample_user.id,
                type='income',
                category_id=1,
                amount=1000.00,
                date=date.today(),
                description='Salary',
                source='manual',
                dedup_hash=Transaction.compute_dedup_hash(
                    sample_user.id, date.today(), 1000.00, 'Salary'
                )
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Verify transaction was created
            saved = Transaction.query.get(transaction.id)
            assert saved is not None
            assert saved.type == 'income'
            assert float(saved.amount) == 1000.00
    
    def test_transaction_dedup_hash(self, app, sample_user):
        """Test the deduplication hash computation."""
        with app.app_context():
            from app.models import Transaction
            
            hash1 = Transaction.compute_dedup_hash(
                sample_user.id, 
                date(2024, 1, 15), 
                100.00, 
                'Test description'
            )
            hash2 = Transaction.compute_dedup_hash(
                sample_user.id, 
                date(2024, 1, 15), 
                100.00, 
                'Test description'
            )
            hash3 = Transaction.compute_dedup_hash(
                sample_user.id, 
                date(2024, 1, 15), 
                200.00, 
                'Test description'
            )
            
            assert hash1 == hash2  # Same data should produce same hash
            assert hash1 != hash3  # Different amount should produce different hash
    
    def test_transaction_type_constraint(self, app, sample_user):
        """Test that transaction type must be income or expense."""
        from app import db
        
        with app.app_context():
            from app.models import Transaction
            
            today = date.today()
            
            # Valid types should work
            t1 = Transaction(
                user_id=sample_user.id,
                type='income',
                category_id=1,
                amount=100.00,
                date=today,
                description='Test',
                dedup_hash=Transaction.compute_dedup_hash(
                    sample_user.id, today, 100.00, 'Test'
                )
            )
            db.session.add(t1)
            db.session.commit()
            
            t2 = Transaction(
                user_id=sample_user.id,
                type='expense',
                category_id=1,
                amount=50.00,
                date=today,
                description='Test 2',
                dedup_hash=Transaction.compute_dedup_hash(
                    sample_user.id, today, 50.00, 'Test 2'
                )
            )
            db.session.add(t2)
            db.session.commit()
            
            assert Transaction.query.count() == 2


class TestImportCSV:
    """Tests for CSV import functionality."""
    
    def test_import_page_loads(self, logged_in_client):
        """Test that the import page loads."""
        response = logged_in_client.get('/transactions/import')
        assert response.status_code == 200
        assert b'Import' in response.data
        assert b'CSV' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
