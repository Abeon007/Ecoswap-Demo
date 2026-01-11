# 🚀 Quick Start Guide - EcoSwap Demo

## Getting Started in 3 Steps:

### 1️⃣ Install Flask
Open your terminal/command prompt and run:
```bash
pip install flask
```

### 2️⃣ Run the Application
Navigate to the project folder and run:
```bash
cd ecoswap-demo
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### 3️⃣ Open in Browser
Go to: **http://localhost:5000**

---

## 🎯 What to Try First:

### Option 1: Login as Admin
1. Click "Sign In"
2. Login with:
   - Email: `admin@ecoswap.com`
   - Password: `admin123`
3. You'll see the Admin Dashboard with stats
4. Click "Users" or "Listings" to manage them

### Option 2: Login as Demo User (Your Account)
1. Click "Sign In"
2. Login with:
   - Email: `user@ecoswap.com`
   - Password: `password123`
3. Browse 20+ pre-loaded listings!
4. Request items from other users

### Option 3: Create a New Account
1. Click "Join Now" on the homepage
2. Fill out the signup form
3. After signup, login with your credentials
4. You'll be taken to the Marketplace

**Pre-loaded Users** (all use password: `password123`):
- sarah.martinez@email.com
- james.kim@email.com  
- maria.lopez@email.com
- david.chen@email.com
- emma.wilson@email.com

---

## 📝 User Features to Test:

1. **Create a Listing**
   - Click "+ New Listing" button
   - Fill in item details
   - Upload an image (optional)
   - Choose Exchange or Donate

2. **Browse Marketplace**
   - Search for items
   - Filter by category
   - Request items from other users
   - 20+ listings already loaded!

3. **Manage Your Listings**
   - Click "My Listings"
   - Edit or delete your items

4. **Handle Requests**
   - Click "My Requests"
   - View requests you sent
   - Accept/decline requests on your items

---

## 🔧 Troubleshooting:

**Problem:** "Port 5000 is already in use"
**Solution:** Edit `app.py`, change the last line to:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Problem:** "Module not found: Flask"
**Solution:** Install Flask:
```bash
pip install flask
```

**Problem:** Want to reset everything?
**Solution:** Delete `ecoswap.db` file and restart the app

---

## 📱 Features Available:

✅ User signup and login
✅ Create/edit/delete listings
✅ Browse and search items
✅ Request items
✅ Accept/decline requests
✅ Admin dashboard
✅ Manage users and listings (admin)
✅ **20+ Pre-loaded sample listings**
✅ **6 Sample users with data**
✅ **SVG icons instead of emojis**

---

## 💡 Tips:

- The marketplace already has 20 listings from 5 different users
- Login as different users to test the exchange workflow
- Upload images to make your listings look better
- Try both "Exchange" and "Donate" listing types
- Test the search and filter functionality
- Admin can see and delete everything

---

## 🎨 Tech Stack:

- Python + Flask (Backend)
- SQLite (Database)
- HTML + CSS + SVG Icons (Frontend)
- No external dependencies needed!

---

Enjoy testing EcoSwap! 🌱
