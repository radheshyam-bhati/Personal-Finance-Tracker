"""Tests for main routes."""
import pytest


class TestDashboard:
    """Tests for the dashboard route."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_dashboard_loads_for_authenticated_user(self, logged_in_client):
        """Test that dashboard loads for authenticated users."""
        response = logged_in_client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_dashboard_shows_empty_state(self, logged_in_client):
        """Test that empty state shows when no transactions exist."""
        response = logged_in_client.get('/')
        assert response.status_code == 200
        # Should show onboarding or empty state
        assert b'import' in response.data.lower() or b'add' in response.data.lower() or b'get your finances' in response.data.lower()
    
    def test_dashboard_with_date_filters(self, logged_in_client):
        """Test that dashboard accepts date filters."""
        response = logged_in_client.get('/?start_date=2024-01-01&end_date=2024-12-31')
        assert response.status_code == 200
        assert b'Dashboard' in response.data


class TestHealth:
    """Tests for the health check endpoint."""
    
    def test_health_endpoint_returns_ok(self, client):
        """Test that the health endpoint returns OK status."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
