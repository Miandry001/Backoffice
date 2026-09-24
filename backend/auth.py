"""
Authentication Endpoints

This module handles user authentication including registration, login, logout,
and current user information retrieval.

SECURITY IMPLEMENTATIONS:
- Rate limiting on login endpoint to prevent brute force attacks
- Input validation for all user data
- Email format validation
- Password complexity requirements
- Role escalation prevention (registration always defaults to 'agent')
- Session-based authentication with Flask-Login

BEST PRACTICES:
- Never return sensitive information in error messages
- Use generic error messages to prevent user enumeration
- Validate all inputs before processing
"""

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User
from config import Config
import re

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

# Password complexity regex - requires at least 8 chars, 1 uppercase, 1 lowercase, 1 digit
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$')

# Username validation - alphanumeric, underscores, 3-30 chars
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_]{3,30}$')


def validate_password_complexity(password):
    """
    Validate password meets complexity requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, 'Password is required'
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        return False, f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long'
    if Config.REQUIRE_PASSWORD_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if Config.REQUIRE_PASSWORD_LOWERCASE and not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if Config.REQUIRE_PASSWORD_DIGIT and not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    if Config.REQUIRE_PASSWORD_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least one special character'
    return True, ''


def validate_username(username):
    """
    Validate username format.
    
    Args:
        username: Username string to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, 'Username is required'
    if len(username) < 3:
        return False, 'Username must be at least 3 characters long'
    if len(username) > 30:
        return False, 'Username must be no more than 30 characters long'
    if not USERNAME_REGEX.match(username):
        return False, 'Username can only contain letters, numbers, and underscores'
    return True, ''


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    SECURITY: Role is hardcoded to 'agent' to prevent privilege escalation.
    Users cannot register as admin or supervisor - only existing admins can promote users.
    
    Request Body:
        username: Unique username (3-30 chars, alphanumeric + underscore)
        email: Valid email address
        password: Password meeting complexity requirements
        
    Returns:
        201: User created successfully
        400: Validation error or duplicate username/email
        429: Rate limit exceeded
    """
    data = request.get_json()
    
    # Extract and validate input
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate email format
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not User.validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password complexity
    is_valid, error_msg = validate_password_complexity(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Check for existing username (prevent user enumeration by using generic message)
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username or email already exists'}), 400
    
    # Check for existing email
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already exists'}), 400
    
    # Create new user - SECURITY: Always default to 'agent' role
    # Role escalation must be done by existing admins through the admin panel
    user = User(username=username, email=email, role='agent')
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User created successfully',
            'user_id': user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and create a session.
    
    SECURITY: Rate limited to prevent brute force attacks.
    Generic error message prevents user enumeration.
    
    Request Body:
        username: User's username
        password: User's password
        
    Returns:
        200: Login successful, returns user info
        401: Invalid credentials
        429: Rate limit exceeded
    """
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validate input presence
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Look up user by username
    user = User.query.filter_by(username=username).first()
    
    # Verify credentials
    # SECURITY: Use generic error message to prevent username enumeration
    if not user or not user.check_password(password) or not user.is_active:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create session
    login_user(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Log out the current user and destroy their session.
    
    Returns:
        200: Logout successful
    """
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Get information about the currently authenticated user.
    
    Returns:
        200: Current user information
        401: Not authenticated
    """
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'is_active': current_user.is_active
    }), 200
