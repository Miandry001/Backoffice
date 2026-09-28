"""
Database Models

This file defines all SQLAlchemy ORM models for the application.
Each model represents a table in the database with appropriate relationships
and constraints.

SECURITY CONSIDERATIONS:
- Passwords are hashed using Werkzeug's pbkdf2:sha256 algorithm
- Email addresses are validated before storage
- Role-based access control is enforced at the model level
- Foreign key constraints ensure data integrity

BEST PRACTICES:
- Use datetime.utcnow for timezone-aware timestamps
- Unique constraints prevent duplicate data
- Indexes on frequently queried columns
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Initialize SQLAlchemy instance - will be configured with the app later
db = SQLAlchemy()

# Email validation regex pattern
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)

    # 🔐 MODIFICATION : Changé en Text pour le chiffrement, nullable=True pour l'initialisation
    # Retrait du unique=True direct car le chiffrement Fernet produit des chaînes uniques à chaque calcul
    email = db.Column(db.Text, nullable=True, index=True)

    # 🔐 AJOUT : Champ pour accueillir le téléphone de récupération chiffré
    phone = db.Column(db.Text, nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='agent', index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    data_records = db.relationship('DataRecord', backref='creator', lazy='dynamic')

    def set_password(self, password):
        if not password or len(password) < 8:
            raise ValueError('Password must be at least 8 characters long')
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def validate_email(email):
        return bool(EMAIL_REGEX.match(email))

    def has_role(self, *roles):
        return self.role in roles

    def __repr__(self):
        return f'<User {self.username}>'


class GoogleSheetConfig(db.Model):
    """
    Configuration for connected Google Sheets.
    
    Stores metadata about Google Sheets that have been connected to the system.
    
    Attributes:
        id: Primary key
        sheet_url: Full URL of the Google Sheet
        sheet_id: Extracted ID from the URL (used for API calls)
        sheet_name: Human-readable name for the sheet
        is_active: Whether this configuration is currently active
        created_at: When the sheet was connected
        updated_at: When the configuration was last updated
    """
    __tablename__ = 'google_sheet_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    sheet_url = db.Column(db.String(500), nullable=False)
    sheet_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    sheet_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<GoogleSheetConfig {self.sheet_name}>'


class Feature(db.Model):
    """
    Feature toggle model for enabling/disabling application features.
    
    Allows administrators to control feature availability without code changes.
    
    Attributes:
        id: Primary key
        name: Unique feature identifier
        description: Human-readable description of the feature
        is_enabled: Whether the feature is currently active
        created_at: When the feature was created
    """
    __tablename__ = 'features'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Feature {self.name} ({"enabled" if self.is_enabled else "disabled"})>'


class ColumnSection(db.Model):
    """
    Configuration for grouping columns into sections.
    
    Divides the 73 columns into 6 logical sections for better data entry UX.
    Each section contains a subset of column indices.
    
    Attributes:
        id: Primary key
        section_name: Human-readable name for the section
        section_order: Display order (1-6)
        columns: JSON array of column indices (e.g., [0, 1, 2, ...])
        is_active: Whether this section is currently active
    """
    __tablename__ = 'column_sections'
    
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(50), nullable=False)
    section_order = db.Column(db.Integer, nullable=False)
    columns = db.Column(db.JSON, nullable=False)  # List of column indices (0-based)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    def __repr__(self):
        return f'<ColumnSection {self.section_name} (order: {self.section_order})>'


class DataRecord(db.Model):
    """
    Cached data records from Google Sheets.
    
    Stores local copies of data for faster access and audit trail.
    
    Attributes:
        id: Primary key
        sheet_id: ID of the Google Sheet this record belongs to
        row_index: Row number in the sheet
        data: JSON object containing the row data
        created_by: User ID who created this record (foreign key)
        created_at: When the record was created
        updated_at: When the record was last updated
    """
    __tablename__ = 'data_records'
    
    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(db.String(100), nullable=False, index=True)
    row_index = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<DataRecord sheet={self.sheet_id} row={self.row_index}>'
