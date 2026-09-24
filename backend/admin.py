"""
Admin Panel Endpoints

This module handles administrative functions including:
- User management (CRUD operations)
- Feature toggle management
- Column section configuration

SECURITY IMPLEMENTATIONS:
- Role-based access control decorators
- Admin-only operations for sensitive functions
- Input validation for all operations
- Protection against self-deletion
- Role validation

BEST PRACTICES:
- Use decorators for reusable permission checks
- Validate all inputs before database operations
- Use database transactions with rollback on error
- Prevent admins from deleting themselves
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Feature, ColumnSection
from auth import validate_username, validate_password_complexity

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)

# Valid roles for validation
VALID_ROLES = ['admin', 'supervisor', 'agent']


def admin_required(f):
    """
    Decorator to require admin role for endpoint access.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function that checks for admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def supervisor_or_admin_required(f):
    """
    Decorator to require supervisor or admin role for endpoint access.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function that checks for supervisor or admin role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin', 'supervisor'):
            return jsonify({'error': 'Supervisor or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """
    List all users in the system.
    
    Only admins can view all users.
    
    Returns:
        200: List of users with their details
    """
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat()
    } for user in users]), 200


@admin_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """
    Create a new user account.
    
    Only admins can create users.
    Validates input and enforces password complexity.
    
    Request Body:
        username: Unique username
        email: Valid email address
        password: Password meeting complexity requirements
        role: User role (admin, supervisor, agent)
        
    Returns:
        201: User created successfully
        400: Validation error
        500: Server error
    """
    data = request.get_json()
    
    # Extract and validate input
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'agent').strip().lower()
    
    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate email
    if not email or not User.validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password
    is_valid, error_msg = validate_password_complexity(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate role
    if role not in VALID_ROLES:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400
    
    # Check for duplicates
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create user
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """
    Update an existing user's information.
    
    Only admins can update users.
    Prevents self-deactivation and validates all changes.
    
    Args:
        user_id: ID of the user to update
        
    Request Body:
        username: Optional new username
        email: Optional new email
        role: Optional new role
        is_active: Optional active status
        password: Optional new password
        
    Returns:
        200: User updated successfully
        400: Validation error
        404: User not found
        500: Server error
    """
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # SECURITY: Prevent admin from deactivating themselves
    if user_id == current_user.id and 'is_active' in data and not data['is_active']:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    # SECURITY: Prevent admin from removing their own admin role
    if user_id == current_user.id and 'role' in data and data['role'] != 'admin':
        return jsonify({'error': 'Cannot remove your own admin role'}), 400
    
    # Update username if provided
    if 'username' in data:
        username = data['username'].strip()
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Check for duplicate username
        existing = User.query.filter_by(username=username).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Username already exists'}), 400
        user.username = username
    
    # Update email if provided
    if 'email' in data:
        email = data['email'].strip().lower()
        if not User.validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check for duplicate email
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email already exists'}), 400
        user.email = email
    
    # Update role if provided
    if 'role' in data:
        role = data['role'].strip().lower()
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400
        user.role = role
    
    # Update active status if provided
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    
    # Update password if provided
    if 'password' in data:
        password = data['password']
        is_valid, error_msg = validate_password_complexity(password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        user.set_password(password)
    
    try:
        db.session.commit()
        return jsonify({'message': 'User updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """
    Delete a user account.
    
    Only admins can delete users.
    Prevents self-deletion.
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        200: User deleted successfully
        400: Cannot delete self
        404: User not found
        500: Server error
    """
    # SECURITY: Prevent admin from deleting themselves
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500


@admin_bp.route('/features', methods=['GET'])
@login_required
@admin_required
def get_features():
    """
    List all feature toggles.
    
    Only admins can view features.
    
    Returns:
        200: List of features
    """
    features = Feature.query.all()
    return jsonify([{
        'id': feature.id,
        'name': feature.name,
        'description': feature.description,
        'is_enabled': feature.is_enabled,
        'created_at': feature.created_at.isoformat()
    } for feature in features]), 200


@admin_bp.route('/features', methods=['POST'])
@login_required
@admin_required
def create_feature():
    """
    Create a new feature toggle.
    
    Only admins can create features.
    
    Request Body:
        name: Unique feature name
        description: Optional description
        is_enabled: Optional initial state (default: False)
        
    Returns:
        201: Feature created
        400: Validation error
        500: Server error
    """
    data = request.get_json()
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Feature name is required'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Feature name must be 100 characters or less'}), 400
    
    # Check for duplicate name
    if Feature.query.filter_by(name=name).first():
        return jsonify({'error': 'Feature name already exists'}), 400
    
    feature = Feature(
        name=name,
        description=data.get('description', '').strip(),
        is_enabled=bool(data.get('is_enabled', False))
    )
    
    try:
        db.session.add(feature)
        db.session.commit()
        return jsonify({'message': 'Feature created', 'feature_id': feature.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create feature'}), 500


@admin_bp.route('/features/<int:feature_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_feature(feature_id):
    """
    Toggle a feature's enabled state.
    
    Only admins can toggle features.
    
    Args:
        feature_id: ID of the feature to toggle
        
    Returns:
        200: Feature toggled
        404: Feature not found
        500: Server error
    """
    feature = Feature.query.get_or_404(feature_id)
    feature.is_enabled = not feature.is_enabled
    
    try:
        db.session.commit()
        return jsonify({'message': 'Feature toggled', 'is_enabled': feature.is_enabled}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle feature'}), 500


@admin_bp.route('/features/<int:feature_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_feature(feature_id):
    """
    Delete a feature toggle.
    
    Only admins can delete features.
    
    Args:
        feature_id: ID of the feature to delete
        
    Returns:
        200: Feature deleted
        404: Feature not found
        500: Server error
    """
    feature = Feature.query.get_or_404(feature_id)
    
    try:
        db.session.delete(feature)
        db.session.commit()
        return jsonify({'message': 'Feature deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete feature'}), 500


@admin_bp.route('/sections', methods=['GET'])
@login_required
def get_sections():
    """
    List all active column sections.
    
    All authenticated users can view sections.
    
    Returns:
        200: List of sections ordered by section_order
    """
    sections = ColumnSection.query.filter_by(is_active=True).order_by(ColumnSection.section_order).all()
    return jsonify([{
        'id': section.id,
        'section_name': section.section_name,
        'section_order': section.section_order,
        'columns': section.columns
    } for section in sections]), 200


@admin_bp.route('/sections', methods=['POST'])
@login_required
@admin_required
def create_section():
    """
    Create a new column section.
    
    Only admins can create sections.
    
    Request Body:
        section_name: Name for the section
        section_order: Display order (1-6)
        columns: Array of column indices
        
    Returns:
        201: Section created
        400: Validation error
        500: Server error
    """
    data = request.get_json()
    
    section_name = data.get('section_name', '').strip()
    section_order = data.get('section_order')
    columns = data.get('columns', [])
    
    if not section_name:
        return jsonify({'error': 'Section name is required'}), 400
    if len(section_name) > 50:
        return jsonify({'error': 'Section name must be 50 characters or less'}), 400
    if not isinstance(section_order, int) or section_order < 1 or section_order > 6:
        return jsonify({'error': 'Section order must be an integer between 1 and 6'}), 400
    if not isinstance(columns, list):
        return jsonify({'error': 'Columns must be an array'}), 400
    if not all(isinstance(col, int) for col in columns):
        return jsonify({'error': 'All column indices must be integers'}), 400
    
    section = ColumnSection(
        section_name=section_name,
        section_order=section_order,
        columns=columns
    )
    
    try:
        db.session.add(section)
        db.session.commit()
        return jsonify({'message': 'Section created', 'section_id': section.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create section'}), 500


@admin_bp.route('/sections/<int:section_id>', methods=['PUT'])
@login_required
@admin_required
def update_section(section_id):
    """
    Update an existing column section.
    
    Only admins can update sections.
    
    Args:
        section_id: ID of the section to update
        
    Request Body:
        section_name: Optional new name
        section_order: Optional new order
        columns: Optional new column array
        is_active: Optional active status
        
    Returns:
        200: Section updated
        400: Validation error
        404: Section not found
        500: Server error
    """
    section = ColumnSection.query.get_or_404(section_id)
    data = request.get_json()
    
    if 'section_name' in data:
        section_name = data['section_name'].strip()
        if not section_name:
            return jsonify({'error': 'Section name cannot be empty'}), 400
        if len(section_name) > 50:
            return jsonify({'error': 'Section name must be 50 characters or less'}), 400
        section.section_name = section_name
    
    if 'section_order' in data:
        section_order = data['section_order']
        if not isinstance(section_order, int) or section_order < 1 or section_order > 6:
            return jsonify({'error': 'Section order must be an integer between 1 and 6'}), 400
        section.section_order = section_order
    
    if 'columns' in data:
        columns = data['columns']
        if not isinstance(columns, list):
            return jsonify({'error': 'Columns must be an array'}), 400
        if not all(isinstance(col, int) for col in columns):
            return jsonify({'error': 'All column indices must be integers'}), 400
        section.columns = columns
    
    if 'is_active' in data:
        section.is_active = bool(data['is_active'])
    
    try:
        db.session.commit()
        return jsonify({'message': 'Section updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update section'}), 500


@admin_bp.route('/sections/<int:section_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_section(section_id):
    """
    Delete a column section.
    
    Only admins can delete sections.
    
    Args:
        section_id: ID of the section to delete
        
    Returns:
        200: Section deleted
        404: Section not found
        500: Server error
    """
    section = ColumnSection.query.get_or_404(section_id)
    
    try:
        db.session.delete(section)
        db.session.commit()
        return jsonify({'message': 'Section deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete section'}), 500
