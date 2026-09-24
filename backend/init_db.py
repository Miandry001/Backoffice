"""
Database Initialization Script

This script initializes the database with:
- Default admin user account
- Default column sections for 73-column data entry

SECURITY NOTE:
- The default admin password should be changed immediately after first login
- This script should only be run once or when resetting the database

USAGE:
    python backend/init_db.py
"""

from app import app
from models import db, User, ColumnSection


def init_database():
    """
    Initialize the database with default data.
    
    Creates all database tables and populates them with:
    1. Default admin user (if not exists)
    2. Default column sections for 73-column data entry (if not exists)
    
    The default admin credentials are:
    - Username: admin
    - Password: Admin@1234 (meets complexity requirements)
    - Email: admin@example.com
    
    SECURITY WARNING: Change the default password immediately after first login!
    """
    with app.app_context():
        # Create all database tables defined in models.py
        # This is safe to run multiple times as it only creates missing tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create default admin user with secure password
            # Password meets complexity requirements:
            # - 8+ characters
            # - Uppercase letter (A)
            # - Lowercase letters (dmin)
            # - Digit (1)
            # - Special character (@)
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('Admin@1234')
            db.session.add(admin)
            print("Created default admin user (username: admin, password: Admin@1234)")
            print("SECURITY WARNING: Change the default password immediately after first login!")
        else:
            print("Admin user already exists, skipping creation")
        
        # Check if column sections already exist
        existing_sections = ColumnSection.query.count()
        if existing_sections == 0:
            # Create 6 sections to divide 73 columns into manageable groups
            # Each section contains approximately 12 columns for better UX
            sections_data = [
                {
                    'section_name': 'Section 1: Basic Information',
                    'section_order': 1,
                    'columns': list(range(0, 12))  # Columns 0-11 (12 columns)
                },
                {
                    'section_name': 'Section 2: Contact Details',
                    'section_order': 2,
                    'columns': list(range(12, 24))  # Columns 12-23 (12 columns)
                },
                {
                    'section_name': 'Section 3: Professional Information',
                    'section_order': 3,
                    'columns': list(range(24, 36))  # Columns 24-35 (12 columns)
                },
                {
                    'section_name': 'Section 4: Financial Data',
                    'section_order': 4,
                    'columns': list(range(36, 48))  # Columns 36-47 (12 columns)
                },
                {
                    'section_name': 'Section 5: Additional Information',
                    'section_order': 5,
                    'columns': list(range(48, 60))  # Columns 48-59 (12 columns)
                },
                {
                    'section_name': 'Section 6: Remarks & Notes',
                    'section_order': 6,
                    'columns': list(range(60, 73))  # Columns 60-72 (13 columns)
                }
            ]
            
            for section_data in sections_data:
                section = ColumnSection(**section_data)
                db.session.add(section)
            
            print("Created 6 default sections for 73 columns")
        else:
            print(f"Column sections already exist ({existing_sections} found), skipping creation")
        
        # Commit all changes to the database
        db.session.commit()
        print("Database initialization completed successfully!")


if __name__ == '__main__':
    """
    Script entry point.
    Run this script to initialize the database with default data.
    """
    init_database()
