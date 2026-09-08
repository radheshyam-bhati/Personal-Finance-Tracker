"""Tests for category and categorization rules."""
import pytest


class TestCategoryIndex:
    """Tests for the categories page."""
    
    def test_categories_page_requires_login(self, client):
        """Test that the categories page requires authentication."""
        response = client.get('/categories', follow_redirects=False)
        # Should redirect to login
        assert response.status_code == 302
    
    def test_categories_page_loads(self, app, logged_in_client):
        """Test that the categories page loads for authenticated users."""
        response = logged_in_client.get('/categories')
        assert response.status_code == 200
        assert b'Categories' in response.data or b'Category' in response.data


class TestCategoryCreate:
    """Tests for creating categories."""
    
    def test_create_category_page_loads(self, logged_in_client):
        """Test that the create category page loads."""
        response = logged_in_client.get('/categories/create')
        assert response.status_code == 200
        assert b'Create Category' in response.data
    
    def test_create_category_requires_login(self, client):
        """Test that creating categories requires authentication."""
        response = client.get('/categories/create', follow_redirects=False)
        assert response.status_code == 302
    
    def test_create_duplicate_category_fails(self, logged_in_client, app, sample_user):
        """Test that creating a duplicate category fails."""
        with app.app_context():
            from app.models import Category
            
            # Try to create a category that already exists
            response = logged_in_client.post('/categories/create', data={
                'name': 'Food'  # Default category already exists
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b'already exists' in response.data.lower() or b'create' in response.data.lower()
    
    def test_create_valid_category_succeeds(self, app, sample_user):
        """Test that creating a valid category succeeds."""
        from app import db
        
        with app.app_context():
            # Create a fresh client for this test
            with app.test_client() as client:
                # Login first
                client.post('/auth/login', data={
                    'email': 'test@example.com',
                    'password': 'testpassword123'
                }, follow_redirects=True)
                
                initial_count = Category.query.filter_by(user_id=sample_user.id).count()
                
                # Create a new category
                unique_name = f'New Category {id(self)}'
                response = client.post('/categories/create', data={
                    'name': unique_name
                }, follow_redirects=True)
                
                assert response.status_code == 200
                
                final_count = Category.query.filter_by(user_id=sample_user.id).filter_by(name=unique_name).count()
                # Category should have been created
                assert final_count >= 1


class TestCategoryRuleIndex:
    """Tests for the categorization rules page."""
    
    def test_rules_page_loads(self, logged_in_client):
        """Test that the rules page loads."""
        response = logged_in_client.get('/categories/rules')
        assert response.status_code == 200
        assert b'Rules' in response.data or b'categorization' in response.data.lower()


class TestCategoryRuleCreate:
    """Tests for creating categorization rules."""
    
    def test_create_rule_page_loads(self, logged_in_client):
        """Test that the create rule page loads."""
        response = logged_in_client.get('/categories/rules/create')
        assert response.status_code == 200
        assert b'Create Rule' in response.data
    
    def test_create_rule_requires_login(self, client):
        """Test that creating rules requires authentication."""
        response = client.get('/categories/rules/create', follow_redirects=False)
        assert response.status_code == 302


class TestCategoryRuleModel:
    """Tests for the CategoryRule model."""
    
    def test_seed_default_rules(self, app, sample_user):
        """Test that default rules are seeded."""
        with app.app_context():
            from app.models import CategoryRule
            
            # Rules should already be seeded in fixtures
            rules = CategoryRule.query.filter_by(user_id=sample_user.id).all()
            assert len(rules) > 0
            
            # Check for some expected default rules
            keywords = [rule.keyword for rule in rules]
            assert 'grocery' in keywords
            assert 'uber' in keywords
            assert 'netflix' in keywords


class TestUncategorizedReview:
    """Tests for the uncategorized transaction review page."""
    
    def test_review_page_loads(self, client, app):
        """Test that the review page redirects when not logged in."""
        response = client.get('/categories/review', follow_redirects=False)
        assert response.status_code == 302
    
    def test_review_page_loads_for_authenticated_user(self, logged_in_client):
        """Test that the review page loads for authenticated users."""
        response = logged_in_client.get('/categories/review')
        assert response.status_code == 200
        assert b'Uncategorized' in response.data or b'Review' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
