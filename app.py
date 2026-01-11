from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import json
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ecoswap-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load translations
translations = {}
locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
for lang in ['en', 'de']:
    try:
        with open(os.path.join(locales_dir, f'{lang}.json'), 'r', encoding='utf-8') as f:
            translations[lang] = json.load(f)
    except Exception as e:
        print(f"Error loading {lang} translation: {e}")
        translations[lang] = {}

def get_t(key):
    lang = session.get('lang', 'en')
    current = translations.get(lang, {})
    keys = key.split('.')
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return key
            
    return current if isinstance(current, str) else key

@app.context_processor
def inject_t():
    return dict(t=get_t, current_lang=session.get('lang', 'en'))

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'de']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))
# Database initialization
def init_db():
    conn = sqlite3.connect('ecoswap.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        display_name TEXT NOT NULL,
        location TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Listings table
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
    
    # Requests table
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        requester_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES listings (id),
        FOREIGN KEY (requester_id) REFERENCES users (id)
    )''')
    
    # Create default admin user if not exists
    c.execute("SELECT * FROM users WHERE email = 'admin@ecoswap.com'")
    if not c.fetchone():
        admin_password = generate_password_hash('admin123')
        c.execute("INSERT INTO users (email, password, display_name, location, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ('admin@ecoswap.com', admin_password, 'Admin', 'System', 1))
    
    conn.commit()
    conn.close()

# Database helper function
def get_db():
    conn = sqlite3.connect('ecoswap.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        display_name = request.form['display_name']
        location = request.form['location']
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if email already exists
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash('Email already registered!', 'error')
            conn.close()
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        c.execute("INSERT INTO users (email, password, display_name, location) VALUES (?, ?, ?, ?)",
                  (email, hashed_password, display_name, location))
        conn.commit()
        conn.close()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['display_name'] = user['display_name']
            session['is_admin'] = user['is_admin']
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('marketplace'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/marketplace')
def marketplace():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get search and filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    listing_type = request.args.get('type', '')
    
    query = '''SELECT l.*, u.display_name, u.location 
               FROM listings l 
               JOIN users u ON l.user_id = u.id 
               WHERE l.status = 'Active' '''
    params = []
    
    if search:
        query += " AND (l.title LIKE ? OR l.description LIKE ?) "
        params.extend([f'%{search}%', f'%{search}%'])
    
    if category:
        query += " AND l.category = ? "
        params.append(category)
    
    if listing_type:
        query += " AND l.listing_type = ? "
        params.append(listing_type)
    
    query += " ORDER BY l.created_at DESC"
    
    c.execute(query, params)
    listings = c.fetchall()
    conn.close()
    
    return render_template('marketplace.html', listings=listings)

@app.route('/my-listings')
def my_listings():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM listings WHERE user_id = ? ORDER BY created_at DESC", 
              (session['user_id'],))
    listings = c.fetchall()
    conn.close()
    
    return render_template('my_listings.html', listings=listings)

@app.route('/create-listing', methods=['GET', 'POST'])
def create_listing():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        condition = request.form['condition']
        listing_type = request.form['listing_type']
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"uploads/{filename}"
        
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO listings (user_id, title, description, category, condition, listing_type, image_path) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (session['user_id'], title, description, category, condition, listing_type, image_path))
        conn.commit()
        conn.close()
        
        flash('Listing created successfully!', 'success')
        return redirect(url_for('my_listings'))
    
    return render_template('create_listing.html')

@app.route('/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        condition = request.form['condition']
        listing_type = request.form['listing_type']
        
        c.execute("""UPDATE listings 
                     SET title=?, description=?, category=?, condition=?, listing_type=?
                     WHERE id=? AND user_id=?""",
                  (title, description, category, condition, listing_type, listing_id, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('my_listings'))
    
    c.execute("SELECT * FROM listings WHERE id=? AND user_id=?", (listing_id, session['user_id']))
    listing = c.fetchone()
    conn.close()
    
    if not listing:
        flash('Listing not found!', 'error')
        return redirect(url_for('my_listings'))
    
    return render_template('edit_listing.html', listing=listing)

@app.route('/delete-listing/<int:listing_id>')
def delete_listing(listing_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM listings WHERE id=? AND user_id=?", (listing_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('my_listings'))

@app.route('/request-item/<int:listing_id>')
def request_item(listing_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Check if user already requested this item
    c.execute("SELECT * FROM requests WHERE listing_id=? AND requester_id=?", 
              (listing_id, session['user_id']))
    if c.fetchone():
        flash('You already requested this item!', 'error')
        conn.close()
        return redirect(url_for('marketplace'))
    
    # Check if user is trying to request their own item
    c.execute("SELECT * FROM listings WHERE id=? AND user_id=?", 
              (listing_id, session['user_id']))
    if c.fetchone():
        flash('You cannot request your own item!', 'error')
        conn.close()
        return redirect(url_for('marketplace'))
    
    c.execute("INSERT INTO requests (listing_id, requester_id) VALUES (?, ?)",
              (listing_id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Request sent successfully!', 'success')
    return redirect(url_for('marketplace'))

@app.route('/my-requests')
def my_requests():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Requests I made
    c.execute('''SELECT r.*, l.title, l.image_path, u.display_name as owner_name
                 FROM requests r
                 JOIN listings l ON r.listing_id = l.id
                 JOIN users u ON l.user_id = u.id
                 WHERE r.requester_id = ?
                 ORDER BY r.request_date DESC''', (session['user_id'],))
    my_requests = c.fetchall()
    
    # Requests on my listings
    c.execute('''SELECT r.*, l.title, l.image_path, u.display_name as requester_name
                 FROM requests r
                 JOIN listings l ON r.listing_id = l.id
                 JOIN users u ON r.requester_id = u.id
                 WHERE l.user_id = ?
                 ORDER BY r.request_date DESC''', (session['user_id'],))
    received_requests = c.fetchall()
    
    conn.close()
    
    return render_template('my_requests.html', my_requests=my_requests, received_requests=received_requests)

@app.route('/handle-request/<int:request_id>/<action>')
def handle_request(request_id, action):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    if action not in ['accept', 'decline']:
        flash('Invalid action!', 'error')
        return redirect(url_for('my_requests'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Verify the request belongs to user's listing
    c.execute('''SELECT r.* FROM requests r
                 JOIN listings l ON r.listing_id = l.id
                 WHERE r.id = ? AND l.user_id = ?''', (request_id, session['user_id']))
    request_data = c.fetchone()
    
    if not request_data:
        flash('Request not found!', 'error')
        conn.close()
        return redirect(url_for('my_requests'))
    
    status = 'Accepted' if action == 'accept' else 'Declined'
    c.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
    
    # If accepted, mark listing as inactive
    if action == 'accept':
        c.execute("UPDATE listings SET status = 'Inactive' WHERE id = ?", (request_data['listing_id'],))
    
    conn.commit()
    conn.close()
    
    flash(f'Request {status.lower()} successfully!', 'success')
    return redirect(url_for('my_requests'))

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = 0")
    total_users = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM listings WHERE status = 'Active'")
    active_listings = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM requests")
    total_requests = c.fetchone()['count']
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users,
                          active_listings=active_listings,
                          total_requests=total_requests)

@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE is_admin = 0 ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/admin/listings')
def admin_listings():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT l.*, u.display_name, u.email 
                 FROM listings l 
                 JOIN users u ON l.user_id = u.id 
                 ORDER BY l.created_at DESC''')
    listings = c.fetchall()
    conn.close()
    
    return render_template('admin/listings.html', listings=listings)

@app.route('/admin/delete-listing/<int:listing_id>')
def admin_delete_listing(listing_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM listings WHERE id=?", (listing_id,))
    conn.commit()
    conn.close()
    
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('admin_listings'))

@app.route('/admin/delete-user/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=? AND is_admin=0", (user_id,))
    conn.commit()
    conn.close()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
