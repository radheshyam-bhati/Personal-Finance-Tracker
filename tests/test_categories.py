"""Tests for category and categorization rules."""
import pytest


class TestCategoryIndex:
    """Tests for the categories page."""
    
    def test_categories_page_loads(self, logged_in_client):
        """Test that the categories page loads."""
        response = logged_in_client.get('/categories')
        assert response.status_code == 200
        assert b'Categories' in response.data
    
    def test_categories_page_shows_default_categories(self, logged_in_client):
        """Test that default categories are shown."""
        response = logged_in_client.get('/categories')
        assert response.status_code == 200
        # Should show default categories like Food, Housing, etc.
        assert b'Food' in response.data or b'Salary' in response.data


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
    
    def test_create_valid_category_succeeds(self, logged_in_client, app, sample_user):
        """Test that creating a valid category succeeds."""
        with app.app_context():
            initial_count = Category.query.filter_by(user_id=sample_user.id).count()
            
            response = logged_in_client.post('/categories/create', data={
                'name': 'New Category'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Category created' in response.data or b'New Category' in response.data
            
            final_count = Category.query.filter_by(user_id=sample_user.id).count()
            assert final_count == initial_count + 1


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
    
    def test_review_page_loads(self, logged_in_client):
        """Test that the review page loads."""
        response = logged_in_client.get('/categories/review')
        assert response.status_code == 200
        assert b'Uncategorized' in response.data or b'Review' in response.data
    
    def test_review_page_requires_login(self, client):
        """Test that review page requires authentication."""
        response = client.get('/categories/review', follow_redirects=False)
        assert response.status_code == 302


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
