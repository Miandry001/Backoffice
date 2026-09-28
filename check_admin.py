import sys
sys.path.append('backend')
from app import app
from models import db, User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Admin user found:")
        print(f"  ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  Is Active: {admin.is_active}")
        print(f"  Password hash: {admin.password_hash[:50]}...")
        
        # Test password check
        test_result = admin.check_password('Admin@1234')
        print(f"  Password check for 'Admin@1234': {test_result}")
    else:
        print("Admin user NOT found in database")
