"""
Data Management Endpoints

This module handles data record management including:
- Retrieving column sections for data entry
- CRUD operations for data records
- Pagination for large datasets

SECURITY IMPLEMENTATIONS:
- Role-based access control for delete operations
- Input validation for all operations
- Sheet ID validation
- Pagination limits to prevent excessive data retrieval

BEST PRACTICES:
- Use pagination for large datasets
- Validate all inputs before database operations
- Use database transactions with rollback on error
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, DataRecord, ColumnSection
from sheets import validate_sheet_id

# Create data blueprint
data_bp = Blueprint('data', __name__)

# Pagination limits
MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 50


@data_bp.route('/sections', methods=['GET'])
@login_required
def get_data_sections():
    """
    Retrieve all active column sections.
    
    All authenticated users can view sections.
    Sections are ordered by section_order for proper display.
    
    Returns:
        200: List of active column sections
    """
    sections = ColumnSection.query.filter_by(is_active=True).order_by(ColumnSection.section_order).all()
    return jsonify([{
        'id': section.id,
        'section_name': section.section_name,
        'section_order': section.section_order,
        'columns': section.columns
    } for section in sections]), 200


@data_bp.route('/records', methods=['GET'])
@login_required
def get_records():
    """
    Retrieve data records with pagination.
    
    All authenticated users can view records.
    Records are filtered by sheet_id and paginated.
    
    Query Parameters:
        sheet_id: ID of the sheet to filter records (required)
        page: Page number (default: 1)
        per_page: Number of records per page (default: 50, max: 100)
        
    Returns:
        200: Paginated list of records
        400: Invalid parameters
    """
    # Validate required parameter
    sheet_id = request.args.get('sheet_id', '').strip()
    if not sheet_id:
        return jsonify({'error': 'Sheet ID is required'}), 400
    
    # Validate sheet ID format
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    
    # Get and validate pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', DEFAULT_PER_PAGE, type=int)
    
    if page < 1:
        return jsonify({'error': 'Page must be at least 1'}), 400
    if per_page < 1 or per_page > MAX_PER_PAGE:
        return jsonify({'error': f'Per page must be between 1 and {MAX_PER_PAGE}'}), 400
    
    try:
        query = DataRecord.query.filter_by(sheet_id=sheet_id)
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'records': [{
                'id': record.id,
                'sheet_id': record.sheet_id,
                'row_index': record.row_index,
                'data': record.data,
                'created_by': record.created_by,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            } for record in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve records'}), 500


@data_bp.route('/records', methods=['POST'])
@login_required
def create_record():
    """
    Create a new data record.
    
    All authenticated users can create records.
    The record is associated with the current user.
    
    Request Body:
        sheet_id: ID of the sheet this record belongs to
        row_index: Row number in the sheet
        data: JSON object containing the record data
        
    Returns:
        201: Record created successfully
        400: Validation error
        500: Server error
    """
    data = request.get_json()
    
    # Validate required fields
    sheet_id = data.get('sheet_id', '').strip()
    row_index = data.get('row_index')
    record_data = data.get('data')
    
    if not sheet_id:
        return jsonify({'error': 'Sheet ID is required'}), 400
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    if not isinstance(row_index, int) or row_index < 1:
        return jsonify({'error': 'Row index must be a positive integer'}), 400
    if not isinstance(record_data, dict):
        return jsonify({'error': 'Data must be a JSON object'}), 400
    
    record = DataRecord(
        sheet_id=sheet_id,
        row_index=row_index,
        data=record_data,
        created_by=current_user.id
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        return jsonify({'message': 'Record created', 'record_id': record.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create record'}), 500


@data_bp.route('/records/<int:record_id>', methods=['PUT'])
@login_required
def update_record(record_id):
    """
    Update an existing data record.
    
    All authenticated users can update records.
    Only the data field can be updated.
    
    Args:
        record_id: ID of the record to update
        
    Request Body:
        data: New JSON object for the record
        
    Returns:
        200: Record updated successfully
        400: Validation error
        404: Record not found
        500: Server error
    """
    record = DataRecord.query.get_or_404(record_id)
    data = request.get_json()
    
    # Validate data field
    if 'data' in data:
        record_data = data['data']
        if not isinstance(record_data, dict):
            return jsonify({'error': 'Data must be a JSON object'}), 400
        record.data = record_data
    else:
        return jsonify({'error': 'Data field is required'}), 400
    
    try:
        db.session.commit()
        return jsonify({'message': 'Record updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update record'}), 500


@data_bp.route('/records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_record(record_id):
    """
    Delete a data record.
    
    Only admins and supervisors can delete records.
    
    Args:
        record_id: ID of the record to delete
        
    Returns:
        200: Record deleted successfully
        403: Insufficient permissions
        404: Record not found
        500: Server error
    """
    # Role-based access control
    if not current_user.has_role('admin', 'supervisor'):
        return jsonify({'error': 'Admin or supervisor access required'}), 403
    
    record = DataRecord.query.get_or_404(record_id)
    
    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Record deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete record'}), 500
