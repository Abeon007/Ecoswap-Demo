"""
Tests for request routes: request-item, my-requests, handle-request
"""
import pytest


class TestRequestItem:
    """Test request item functionality."""
    
    def test_request_item_requires_login(self, client, test_listing):
        """Test that requesting an item requires authentication."""
        response = client.get(f'/request-item/{test_listing["id"]}', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_request_item_success(self, logged_in_user, test_listing):
        """Test successful item request."""
        # Create a different user for the listing owner
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('owner123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('owner1@example.com', password_hash, 'Owner', 'Owner City'))
        owner_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (owner_id, 'Owner Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        conn.close()
        
        response = logged_in_user.get(f'/request-item/{listing_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that request was created
        conn = get_db()
        c = conn.cursor()
        with logged_in_user.session_transaction() as sess:
            user_id = sess.get('user_id')
        
        c.execute("SELECT * FROM requests WHERE listing_id = ? AND requester_id = ?", 
                  (listing_id, user_id))
        request = c.fetchone()
        conn.close()
        
        assert request is not None
        assert request['status'] == 'Pending'
    
    def test_request_item_own_listing(self, logged_in_user, test_listing):
        """Test that user cannot request their own listing."""
        from app import get_db
        
        response = logged_in_user.get(f'/request-item/{test_listing["id"]}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that request was NOT created
        conn = get_db()
        c = conn.cursor()
        with logged_in_user.session_transaction() as sess:
            user_id = sess.get('user_id')
        
        c.execute("SELECT * FROM requests WHERE listing_id = ? AND requester_id = ?", 
                  (test_listing['id'], user_id))
        request = c.fetchone()
        conn.close()
        
        assert request is None
    
    def test_request_item_duplicate(self, logged_in_user, test_listing):
        """Test that user cannot request the same item twice."""
        # Create a different user for the listing owner
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('owner123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('owner2@example.com', password_hash, 'Owner', 'Owner City'))
        owner_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (owner_id, 'Owner Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        conn.close()
        
        # Make first request
        logged_in_user.get(f'/request-item/{listing_id}', follow_redirects=True)
        
        # Try to request again
        response = logged_in_user.get(f'/request-item/{listing_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that only one request exists
        conn = get_db()
        c = conn.cursor()
        with logged_in_user.session_transaction() as sess:
            user_id = sess.get('user_id')
        
        c.execute("SELECT COUNT(*) as count FROM requests WHERE listing_id = ? AND requester_id = ?", 
                  (listing_id, user_id))
        count = c.fetchone()['count']
        conn.close()
        
        assert count == 1


class TestMyRequests:
    """Test my-requests functionality."""
    
    def test_my_requests_requires_login(self, client):
        """Test that my-requests requires authentication."""
        response = client.get('/my-requests', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_my_requests_loads(self, logged_in_user):
        """Test that my-requests page loads."""
        response = logged_in_user.get('/my-requests')
        assert response.status_code == 200
    
    def test_my_requests_shows_sent_requests(self, logged_in_user, test_listing):
        """Test that my-requests shows requests user sent."""
        # Create a request
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('owner123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('owner3@example.com', password_hash, 'Owner', 'Owner City'))
        owner_id = c.lastrowid
        
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (owner_id, 'Owner Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        
        with logged_in_user.session_transaction() as sess:
            user_id = sess.get('user_id')
        
        c.execute("INSERT INTO requests (listing_id, requester_id, status) VALUES (?, ?, ?)",
                  (listing_id, user_id, 'Pending'))
        conn.commit()
        conn.close()
        
        response = logged_in_user.get('/my-requests')
        assert response.status_code == 200
    
    def test_my_requests_shows_received_requests(self, logged_in_user, test_listing, test_request):
        """Test that my-requests shows requests received on user's listings."""
        response = logged_in_user.get('/my-requests')
        assert response.status_code == 200
        assert b'request' in response.data.lower()


class TestHandleRequest:
    """Test handle request functionality."""
    
    def test_handle_request_requires_login(self, client, test_request):
        """Test that handle request requires authentication."""
        response = client.get(f'/handle-request/{test_request["id"]}/accept', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_accept_request_success(self, logged_in_user, test_listing, test_request):
        """Test successfully accepting a request."""
        from app import get_db
        
        response = logged_in_user.get(f'/handle-request/{test_request["id"]}/accept', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that request status was updated
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (test_request['id'],))
        request = c.fetchone()
        
        assert request is not None
        assert request['status'] == 'Accepted'
        
        # Check that listing was marked as inactive
        c.execute("SELECT * FROM listings WHERE id = ?", (test_listing['id'],))
        listing = c.fetchone()
        conn.close()
        
        assert listing is not None
        assert listing['status'] == 'Inactive'
    
    def test_decline_request_success(self, logged_in_user, test_listing, test_request):
        """Test successfully declining a request."""
        from app import get_db
        
        response = logged_in_user.get(f'/handle-request/{test_request["id"]}/decline', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that request status was updated
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (test_request['id'],))
        request = c.fetchone()
        conn.close()
        
        assert request is not None
        assert request['status'] == 'Declined'
        
        # Check that listing is still active
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM listings WHERE id = ?", (test_listing['id'],))
        listing = c.fetchone()
        conn.close()
        
        assert listing is not None
        assert listing['status'] == 'Active'
    
    def test_handle_request_invalid_action(self, logged_in_user, test_request):
        """Test handle request with invalid action."""
        response = logged_in_user.get(f'/handle-request/{test_request["id"]}/invalid', follow_redirects=True)
        assert response.status_code == 200
    
    def test_handle_request_not_owner(self, logged_in_user, test_request):
        """Test that user cannot handle requests on listings they don't own."""
        # Create another user
        from werkzeug.security import generate_password_hash
        from app import get_db
        
        conn = get_db()
        c = conn.cursor()
        
        password_hash = generate_password_hash('other123')
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  ('other4@example.com', password_hash, 'Other User', 'Other City'))
        other_user_id = c.lastrowid
        
        # Create listing and request by other user
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type) 
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (other_user_id, 'Other Item', 'Description', 'Electronics', 'New', 'Exchange'))
        conn.commit()
        listing_id = c.lastrowid
        
        c.execute("INSERT INTO requests (listing_id, requester_id, status) VALUES (?, ?, ?)",
                  (listing_id, other_user_id, 'Pending'))
        conn.commit()
        other_request_id = c.lastrowid
        conn.close()
        
        # Try to handle other user's request
        response = logged_in_user.get(f'/handle-request/{other_request_id}/accept', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that request was NOT updated
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (other_request_id,))
        request = c.fetchone()
        conn.close()
        
        assert request is not None
        assert request['status'] == 'Pending'  # Should still be pending
