"""Tests for authentication routes."""
import pytest


class TestLogin:
    """Tests for the login route."""
    
    def test_login_page_loads(self, client):
        """Test that the login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Email' in response.data
    
    def test_login_with_authenticated_user_redirects(self, logged_in_client):
        """Test that authenticated users are redirected from login."""
        response = logged_in_client.get('/auth/login', follow_redirects=False)
        assert response.status_code == 302
        assert '/auth/login' not in response.location


class TestSignup:
    """Tests for the signup route."""
    
    def test_signup_page_loads(self, client):
        """Test that the signup page loads correctly."""
        response = client.get('/auth/signup')
        assert response.status_code == 200
        assert b'Create Account' in response.data
    
    def test_signup_with_authenticated_user_redirects(self, logged_in_client):
        """Test that authenticated users are redirected from signup."""
        response = logged_in_client.get('/auth/signup', follow_redirects=False)
        assert response.status_code == 302


class TestLogout:
    """Tests for the logout route."""
    
    def test_logout_clears_session(self, logged_in_client, app):
        """Test that logout clears the user session."""
        response = logged_in_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out' in response.data.lower()


class TestProfile:
    """Tests for the profile route."""
    
    def test_profile_requires_login(self, client):
        """Test that profile page requires authentication."""
        response = client.get('/auth/profile', follow_redirects=False)
        assert response.status_code == 302
    
    def test_profile_loads_for_authenticated_user(self, logged_in_client):
        """Test that profile page loads for authenticated users."""
        response = logged_in_client.get('/auth/profile')
        assert response.status_code == 200
        assert b'Profile' in response.data


class TestGoogleOAuth:
    """Tests for Google OAuth routes."""
    
    def test_google_login_route_exists(self, client):
        """Test that Google login route exists."""
        response = client.get('/auth/login/google', follow_redirects=False)
        # Should redirect to Google
        assert response.status_code in [302, 400]  # 400 if OAuth not configured


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
