# EcoSwap Demo - Sustainable Item Exchange Platform

A simple demo website for EcoSwap, a platform that facilitates item exchange and donation within communities.

## Features

### User Features:
- Sign up and login
- Create, edit, and delete item listings
- Browse and search marketplace
- Filter by category and listing type
- Request items from other users
- Accept/decline requests on your listings
- View sent and received requests

### Admin Features:
- Admin dashboard with statistics
- View all users
- View all listings
- Delete users and listings

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open in Browser
Open your browser and go to:
```
http://localhost:5000
```

## Demo Credentials

### Admin Account:
- Email: `admin@ecoswap.com`
- Password: `admin123`

### Your User Account:
- Email: `user@ecoswap.com`
- Password: `password123`

### Other Test Users (all use password: password123):
- sarah.martinez@email.com
- james.kim@email.com
- maria.lopez@email.com
- david.chen@email.com
- emma.wilson@email.com

The database comes pre-populated with 20 sample listings from various users across different categories!

### Create User Account:
You can also create your own user account through the signup page.

## Project Structure
```
ecoswap-demo/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── ecoswap.db            # SQLite database (created automatically)
├── static/
│   ├── css/
│   │   └── style.css     # All styling
│   └── uploads/          # Uploaded images
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Landing page
    ├── login.html        # Login page
    ├── signup.html       # Signup page
    ├── marketplace.html  # Browse listings
    ├── my_listings.html  # User's listings
    ├── create_listing.html
    ├── edit_listing.html
    ├── my_requests.html  # Requests management
    └── admin/
        ├── dashboard.html
        ├── users.html
        └── listings.html
```

## Database Schema

### Users Table:
- id, email, password, display_name, location, is_admin, created_at

### Listings Table:
- id, user_id, title, description, category, condition, listing_type, status, image_path, created_at

### Requests Table:
- id, listing_id, requester_id, status, request_date

## Technologies Used
- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Werkzeug password hashing

## Features In Scope
✅ User registration and login
✅ Creation, viewing, editing, and deletion of item listings
✅ Browsing and searching all active listings
✅ Simple item request and approval system
✅ Simplified tracking of user listings and requests

## Features Out of Scope (Not Implemented)
❌ User profiles showing listing history and earned eco-points
❌ Eco-points system to track user activity
❌ User-to-user messaging or chat functionality
❌ Community forums or discussion boards
❌ Liking or favoriting items
❌ User reviews and rating systems
❌ Financial transactions or payment processing
❌ Mobile application
❌ Physical logistics or shipping coordination

## Notes
- This is a demo application for development and testing purposes
- Images uploaded are stored in the `static/uploads` folder
- The database is reset when you delete `ecoswap.db`
- For production use, additional security measures should be implemented

## Troubleshooting

### Port already in use:
If port 5000 is already in use, edit `app.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001 or any available port
```

### Database errors:
Delete `ecoswap.db` and restart the application to recreate the database:
```bash
rm ecoswap.db
python app.py
```

## Support
For issues or questions, please refer to the project documentation or contact the development team.
