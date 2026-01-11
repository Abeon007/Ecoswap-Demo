import pytest
import sqlite3
import os
import tempfile
import shutil
from app import app

# Global variable to store test database path
_test_db_path = None

@pytest.fixture(scope='function', autouse=True)
def setup_test_db(monkeypatch):
    """Set up a test database for each test."""
    global _test_db_path
    
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    _test_db_path = db_path
    upload_dir = tempfile.mkdtemp()
    
    # Configure test app
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize test database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables (same as in app.py)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        display_name TEXT NOT NULL,
        location TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        condition TEXT NOT NULL,
        listing_type TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        requester_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES listings (id),
        FOREIGN KEY (requester_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()
    
    # Monkey patch get_db to use test database with timeout
    def get_test_db():
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Replace get_db in app module
    import app as app_module
    monkeypatch.setattr(app_module, 'get_db', get_test_db)
    
    yield
    
    # Cleanup
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except:
        pass
    try:
        shutil.rmtree(upload_dir)
    except:
        pass
    _test_db_path = None

@pytest.fixture
def client():
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def test_user():
    """Create a test user and return credentials."""
    from werkzeug.security import generate_password_hash
    from app import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    password_hash = generate_password_hash('testpass123')
    c.execute("INSERT INTO users (email, password, display_name, location, is_admin) VALUES (?, ?, ?, ?, ?)",
              ('testuser@example.com', password_hash, 'Test User', 'Test City', 0))
    conn.commit()
    
    user_id = c.lastrowid
    conn.close()
    
    return {
        'id': user_id,
        'email': 'testuser@example.com',
        'password': 'testpass123',
        'display_name': 'Test User',
        'location': 'Test City',
        'is_admin': 0
    }

@pytest.fixture
def test_admin():
    """Create a test admin user and return credentials."""
    from werkzeug.security import generate_password_hash
    from app import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    password_hash = generate_password_hash('adminpass123')
    c.execute("INSERT INTO users (email, password, display_name, location, is_admin) VALUES (?, ?, ?, ?, ?)",
              ('admin@test.com', password_hash, 'Admin User', 'Admin City', 1))
    conn.commit()
    
    user_id = c.lastrowid
    conn.close()
    
    return {
        'id': user_id,
        'email': 'admin@test.com',
        'password': 'adminpass123',
        'display_name': 'Admin User',
        'location': 'Admin City',
        'is_admin': 1
    }

@pytest.fixture
def logged_in_user(client, test_user):
    """Log in a test user and return the client with session."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user['id']
        sess['display_name'] = test_user['display_name']
        sess['is_admin'] = test_user['is_admin']
    return client

@pytest.fixture
def logged_in_admin(client, test_admin):
    """Log in a test admin and return the client with session."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_admin['id']
        sess['display_name'] = test_admin['display_name']
        sess['is_admin'] = test_admin['is_admin']
    return client

@pytest.fixture
def test_listing(test_user):
    """Create a test listing."""
    from app import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type, status) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (test_user['id'], 'Test Item', 'Test Description', 'Electronics', 'New', 'Exchange', 'Active'))
    conn.commit()
    
    listing_id = c.lastrowid
    conn.close()
    
    return {
        'id': listing_id,
        'user_id': test_user['id'],
        'title': 'Test Item',
        'description': 'Test Description',
        'category': 'Electronics',
        'condition': 'New',
        'listing_type': 'Exchange',
        'status': 'Active'
    }

@pytest.fixture
def test_request(test_user, test_listing):
    """Create a test request from another user."""
    from werkzeug.security import generate_password_hash
    from app import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    # Create another user to make the request
    password_hash = generate_password_hash('requester123')
    c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
              ('requester@example.com', password_hash, 'Requester', 'Requester City'))
    requester_id = c.lastrowid
    
    # Create the request
    c.execute("INSERT INTO requests (listing_id, requester_id, status) VALUES (?, ?, ?)",
              (test_listing['id'], requester_id, 'Pending'))
    conn.commit()
    
    request_id = c.lastrowid
    conn.close()
    
    return {
        'id': request_id,
        'listing_id': test_listing['id'],
        'requester_id': requester_id,
        'status': 'Pending'
    }
