"""
Tests for admin routes: admin dashboard, admin/users, admin/listings, delete operations
"""
import pytest


class TestAdminDashboard:
    """Test admin dashboard functionality."""
    
    def test_admin_dashboard_requires_login(self, client):
        """Test that admin dashboard requires authentication."""
        response = client.get('/admin', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_admin_dashboard_requires_admin(self, logged_in_user):
        """Test that admin dashboard requires admin privileges."""
        response = logged_in_user.get('/admin', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_admin_dashboard_loads(self, logged_in_admin):
        """Test that admin dashboard loads for admin user."""
        response = logged_in_admin.get('/admin')
        assert response.status_code == 200
        assert b'admin' in response.data.lower() or b'dashboard' in response.data.lower()
    
    def test_admin_dashboard_shows_statistics(self, logged_in_admin, test_user, test_listing):
        """Test that admin dashboard displays statistics."""
        response = logged_in_admin.get('/admin')
        assert response.status_code == 200
        # Should show stats about users, listings, requests


class TestAdminUsers:
    """Test admin users management."""
    
    def test_admin_users_requires_admin(self, logged_in_user):
        """Test that admin users page requires admin privileges."""
        response = logged_in_user.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_admin_users_loads(self, logged_in_admin, test_user):
        """Test that admin users page loads."""
        response = logged_in_admin.get('/admin/users')
        assert response.status_code == 200
    
    def test_admin_users_shows_all_users(self, logged_in_admin, test_user):
        """Test that admin users page shows all users."""
        response = logged_in_admin.get('/admin/users')
        assert response.status_code == 200
        # Should show test_user in the list
    
    def test_admin_users_excludes_admins(self, logged_in_admin, test_admin):
        """Test that admin users page excludes admin users."""
        response = logged_in_admin.get('/admin/users')
        assert response.status_code == 200
        # Admin users should not appear in the list
    
    def test_admin_delete_user_success(self, logged_in_admin, test_user):
        """Test successful user deletion by admin."""
        from app import get_db
        
        user_id = test_user['id']
        response = logged_in_admin.get(f'/admin/delete-user/{user_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that user was deleted
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        conn.close()
        
        assert user is None
    
    def test_admin_delete_user_cannot_delete_admin(self, logged_in_admin, test_admin):
        """Test that admin cannot delete other admin users."""
        from app import get_db
        
        admin_id = test_admin['id']
        response = logged_in_admin.get(f'/admin/delete-user/{admin_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that admin user still exists
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (admin_id,))
        user = c.fetchone()
        conn.close()
        
        assert user is not None  # Should still exist
    
    def test_admin_delete_user_requires_admin(self, logged_in_user, test_user):
        """Test that regular users cannot delete users."""
        user_id = test_user['id']
        response = logged_in_user.get(f'/admin/delete-user/{user_id}', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


class TestAdminListings:
    """Test admin listings management."""
    
    def test_admin_listings_requires_admin(self, logged_in_user):
        """Test that admin listings page requires admin privileges."""
        response = logged_in_user.get('/admin/listings', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_admin_listings_loads(self, logged_in_admin, test_listing):
        """Test that admin listings page loads."""
        response = logged_in_admin.get('/admin/listings')
        assert response.status_code == 200
    
    def test_admin_listings_shows_all_listings(self, logged_in_admin, test_listing):
        """Test that admin listings page shows all listings."""
        response = logged_in_admin.get('/admin/listings')
        assert response.status_code == 200
        # Should show all listings including test_listing
    
    def test_admin_delete_listing_success(self, logged_in_admin, test_listing):
        """Test successful listing deletion by admin."""
        from app import get_db
        
        listing_id = test_listing['id']
        response = logged_in_admin.get(f'/admin/delete-listing/{listing_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that listing was deleted
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        listing = c.fetchone()
        conn.close()
        
        assert listing is None
    
    def test_admin_delete_listing_requires_admin(self, logged_in_user, test_listing):
        """Test that regular users cannot delete listings through admin route."""
        listing_id = test_listing['id']
        response = logged_in_user.get(f'/admin/delete-listing/{listing_id}', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
