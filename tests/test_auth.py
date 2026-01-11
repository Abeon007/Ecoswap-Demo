"""
Tests for authentication routes: login, signup, logout
"""
import pytest
from werkzeug.security import generate_password_hash


class TestSignup:
    """Test user signup functionality."""
    
    def test_signup_page_loads(self, client):
        """Test that signup page loads successfully."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'signup' in response.data.lower() or b'join' in response.data.lower()
    
    def test_signup_success(self, client):
        """Test successful user registration."""
        from app import get_db
        
        response = client.post('/signup', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'display_name': 'New User',
            'location': 'New City'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that user was created in database
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", ('newuser@example.com',))
        user = c.fetchone()
        conn.close()
        
        assert user is not None
        assert user['email'] == 'newuser@example.com'
        assert user['display_name'] == 'New User'
        assert user['location'] == 'New City'
        assert user['is_admin'] == 0
    
    def test_signup_duplicate_email(self, client, test_user):
        """Test that duplicate email registration fails."""
        from app import get_db
        
        response = client.post('/signup', data={
            'email': test_user['email'],
            'password': 'password123',
            'display_name': 'Another User',
            'location': 'Another City'
        })
        
        # Should redirect back to signup with error
        assert response.status_code in [302, 200]
        
        # Check that only one user exists with that email
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM users WHERE email = ?", (test_user['email'],))
        count = c.fetchone()['count']
        conn.close()
        
        assert count == 1
    
    def test_signup_missing_fields(self, client):
        """Test that signup fails with missing required fields."""
        response = client.post('/signup', data={
            'email': 'incomplete@example.com',
            'password': 'password123'
            # Missing display_name and location
        })
        
        # Should return error or redirect
        assert response.status_code in [400, 500, 302]


class TestLogin:
    """Test user login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()
    
    def test_login_success_regular_user(self, client, test_user):
        """Test successful login for regular user."""
        response = client.post('/login', data={
            'email': test_user['email'],
            'password': test_user['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that session was created
        with client.session_transaction() as sess:
            assert sess.get('user_id') == test_user['id']
            assert sess.get('display_name') == test_user['display_name']
            assert sess.get('is_admin') == 0
    
    def test_login_success_admin(self, client, test_admin):
        """Test successful login for admin user."""
        response = client.post('/login', data={
            'email': test_admin['email'],
            'password': test_admin['password']
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that session was created with admin flag
        with client.session_transaction() as sess:
            assert sess.get('user_id') == test_admin['id']
            assert sess.get('is_admin') == 1
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code in [200, 302]
        # Should show error message
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/login', data={
            'email': test_user['email'],
            'password': 'wrongpassword'
        })
        
        assert response.status_code in [200, 302]
        
        # Check that session was NOT created
        with client.session_transaction() as sess:
            assert sess.get('user_id') is None
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post('/login', data={
            'email': 'test@example.com'
            # Missing password
        })
        
        assert response.status_code in [400, 500, 302]


class TestLogout:
    """Test user logout functionality."""
    
    def test_logout_requires_login(self, client):
        """Test that logout redirects if not logged in."""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_logout_clears_session(self, logged_in_user):
        """Test that logout clears user session."""
        # Verify user is logged in
        with logged_in_user.session_transaction() as sess:
            assert sess.get('user_id') is not None
        
        # Logout
        response = logged_in_user.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify session is cleared
        with logged_in_user.session_transaction() as sess:
            assert sess.get('user_id') is None
            assert sess.get('display_name') is None
            assert sess.get('is_admin') is None
    
    def test_logout_redirects_to_index(self, logged_in_user):
        """Test that logout redirects to index page."""
        response = logged_in_user.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/index' in response.location or '/' in response.location


class TestIndex:
    """Test index/home page."""
    
    def test_index_page_loads(self, client):
        """Test that index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_accessible_without_login(self, client):
        """Test that index page is accessible without login."""
        response = client.get('/')
        assert response.status_code == 200
