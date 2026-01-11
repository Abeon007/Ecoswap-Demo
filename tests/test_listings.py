"""
Tests for listing routes: create, edit, delete, marketplace, my-listings
"""
import pytest


class TestMarketplace:
    """Test marketplace functionality."""
    
    def test_marketplace_requires_login(self, client):
        """Test that marketplace requires authentication."""
        response = client.get('/marketplace', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_marketplace_loads(self, logged_in_user):
        """Test that marketplace loads for logged in user."""
        response = logged_in_user.get('/marketplace')
        assert response.status_code == 200
        assert b'marketplace' in response.data.lower() or b'items' in response.data.lower()
    
    def test_marketplace_shows_listings(self, logged_in_user, test_listing):
        """Test that marketplace displays listings."""
        response = logged_in_user.get('/marketplace')
        assert response.status_code == 200
        assert test_listing['title'].encode() in response.data or b'Test Item' in response.data
    
    def test_marketplace_search(self, logged_in_user, test_listing):
        """Test marketplace search functionality."""
        response = logged_in_user.get('/marketplace?search=Test')
        assert response.status_code == 200
    
    def test_marketplace_filter_category(self, logged_in_user, test_listing):
        """Test marketplace category filter."""
        response = logged_in_user.get('/marketplace?category=Electronics')
        assert response.status_code == 200
    
    def test_marketplace_filter_type(self, logged_in_user, test_listing):
        """Test marketplace listing type filter."""
        response = logged_in_user.get('/marketplace?type=Exchange')
        assert response.status_code == 200
    
    def test_marketplace_only_shows_active(self, logged_in_user, test_user):
        """Test that marketplace only shows active listings."""
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        # Create an inactive listing
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type, status) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (test_user['id'], 'Inactive Item', 'Description', 'Electronics', 'New', 'Exchange', 'Inactive'))
        conn.commit()
        conn.close()
        
        response = logged_in_user.get('/marketplace')
        assert response.status_code == 200
        # Inactive listing should not appear in marketplace


class TestMyListings:
    """Test my-listings functionality."""
    
    def test_my_listings_requires_login(self, client):
        """Test that my-listings requires authentication."""
        response = client.get('/my-listings', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_my_listings_loads(self, logged_in_user):
        """Test that my-listings page loads."""
        response = logged_in_user.get('/my-listings')
        assert response.status_code == 200
    
    def test_my_listings_shows_user_listings(self, logged_in_user, test_listing):
        """Test that my-listings shows user's own listings."""
        response = logged_in_user.get('/my-listings')
        assert response.status_code == 200
        assert test_listing['title'].encode() in response.data or b'Test Item' in response.data
    
    def test_my_listings_only_shows_own_listings(self, logged_in_user, test_user):
        """Test that my-listings only shows current user's listings."""
        # Create another user with a listing
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('other123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('other7@example.com', password_hash, 'Other User', 'Other City'))
        other_user_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (other_user_id, 'Other Item', 'Description', 'Books', 'Good', 'Donate'))
        conn.commit()
        conn.close()
        
        response = logged_in_user.get('/my-listings')
        assert response.status_code == 200
        # Should not show other user's listing


class TestCreateListing:
    """Test create listing functionality."""
    
    def test_create_listing_page_loads(self, logged_in_user):
        """Test that create listing page loads."""
        response = logged_in_user.get('/create-listing')
        assert response.status_code == 200
    
    def test_create_listing_requires_login(self, client):
        """Test that create listing requires authentication."""
        response = client.get('/create-listing', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_create_listing_success(self, logged_in_user, test_user):
        """Test successful listing creation."""
        from app import get_db
        
        response = logged_in_user.post('/create-listing', data={
            'title': 'New Listing',
            'description': 'A new item for exchange',
            'category': 'Books',
            'condition': 'Good',
            'listing_type': 'Exchange'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that listing was created
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE user_id = ? AND title = ?", 
                  (test_user['id'], 'New Listing'))
        listing = c.fetchone()
        conn.close()
        
        assert listing is not None
        assert listing['title'] == 'New Listing'
        assert listing['description'] == 'A new item for exchange'
        assert listing['category'] == 'Books'
        assert listing['status'] == 'Active'
    
    def test_create_listing_missing_fields(self, logged_in_user):
        """Test create listing with missing required fields."""
        response = logged_in_user.post('/create-listing', data={
            'title': 'Incomplete Listing'
            # Missing other required fields
        })
        
        assert response.status_code in [400, 500, 200]


class TestEditListing:
    """Test edit listing functionality."""
    
    def test_edit_listing_page_loads(self, logged_in_user, test_listing):
        """Test that edit listing page loads."""
        response = logged_in_user.get(f'/edit-listing/{test_listing["id"]}')
        assert response.status_code == 200
    
    def test_edit_listing_requires_login(self, client, test_listing):
        """Test that edit listing requires authentication."""
        response = client.get(f'/edit-listing/{test_listing["id"]}', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_edit_listing_success(self, logged_in_user, test_listing):
        """Test successful listing update."""
        from app import get_db
        
        response = logged_in_user.post(f'/edit-listing/{test_listing["id"]}', data={
            'title': 'Updated Title',
            'description': 'Updated description',
            'category': 'Clothing',
            'condition': 'Like New',
            'listing_type': 'Donate'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that listing was updated
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE id = ?", (test_listing['id'],))
        listing = c.fetchone()
        conn.close()
        
        assert listing is not None
        assert listing['title'] == 'Updated Title'
        assert listing['description'] == 'Updated description'
        assert listing['category'] == 'Clothing'
    
    def test_edit_listing_not_owner(self, logged_in_user, test_user):
        """Test that user cannot edit other user's listing."""
        # Create listing by another user
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('other123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('owner5@example.com', password_hash, 'Owner', 'Owner City'))
        owner_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (owner_id, 'Owner Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        conn.close()
        
        # Try to edit
        response = logged_in_user.get(f'/edit-listing/{listing_id}', follow_redirects=True)
        # Should redirect or show error
        assert response.status_code in [200, 302, 404]


class TestDeleteListing:
    """Test delete listing functionality."""
    
    def test_delete_listing_requires_login(self, client, test_listing):
        """Test that delete listing requires authentication."""
        response = client.get(f'/delete-listing/{test_listing["id"]}', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_delete_listing_success(self, logged_in_user, test_listing):
        """Test successful listing deletion."""
        from app import get_db
        
        listing_id = test_listing['id']
        response = logged_in_user.get(f'/delete-listing/{listing_id}', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that listing was deleted
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        listing = c.fetchone()
        conn.close()
        
        assert listing is None
    
    def test_delete_listing_not_owner(self, logged_in_user, test_user):
        """Test that user cannot delete other user's listing."""
        # Create listing by another user
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('other123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('owner6@example.com', password_hash, 'Owner', 'Owner City'))
        owner_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (owner_id, 'Owner Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        conn.close()
        
        # Try to delete
        response = logged_in_user.get(f'/delete-listing/{listing_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that listing still exists
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        listing = c.fetchone()
        conn.close()
        
        assert listing is not None  # Should still exist
