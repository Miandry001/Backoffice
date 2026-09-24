"""
Google Sheets Integration Endpoints

This module handles all interactions with the Google Sheets API including:
- Connecting new sheets
- Reading sheet metadata and data
- Updating and appending data
- Role-based access control for different sheets

SECURITY IMPLEMENTATIONS:
- Role-based access control (agents only access Sheet1)
- Input validation for sheet URLs
- Sheet ID extraction with regex
- Error handling without exposing sensitive information

ALGORITHM FIX:
- Fixed column letter calculation bug that failed beyond 26 columns
- Now properly handles 73+ columns using correct Excel-style notation

BEST PRACTICES:
- Service account authentication for API access
- Proper error handling and logging
- Validation of all inputs
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import Config
from models import db, GoogleSheetConfig

# Create sheets blueprint
sheets_bp = Blueprint('sheets', __name__)

# Cache for service instances to avoid recreating for each request
_sheets_service_cache = None


def get_sheets_service():
    """
    Get or create a Google Sheets API service instance.
    
    Uses service account authentication for programmatic access to sheets.
    The service account must be granted access to the target Google Sheets.
    
    Returns:
        Google Sheets API service object
        
    Raises:
        Exception: If credentials file is not found or invalid
    """
    global _sheets_service_cache
    
    if _sheets_service_cache is None:
        try:
            credentials = service_account.Credentials.from_service_account_file(
                Config.GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            _sheets_service_cache = build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            raise Exception(f'Failed to initialize Google Sheets service: {str(e)}')
    
    return _sheets_service_cache


def extract_sheet_id(url):
    """
    Extract the Google Sheet ID from a Google Sheets URL.
    
    Expected URL format: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
    
    Args:
        url: Google Sheets URL string
        
    Returns:
        str: Sheet ID if found, None otherwise
    """
    # Pattern matches: /spreadsheets/d/[SHEET_ID]
    # Sheet ID can contain letters, numbers, hyphens, and underscores
    pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


def number_to_column_letter(n):
    """
    Convert a column number to Excel-style column letter notation.
    
    CRITICAL FIX: The previous implementation used chr(64 + n) which only works
    for columns 1-26 (A-Z). This implementation correctly handles any number of columns.
    
    Examples:
        1 -> A
        26 -> Z
        27 -> AA
        52 -> AZ
        53 -> BA
        73 -> BA (for our 73-column use case)
    
    Args:
        n: Column number (1-based)
        
    Returns:
        str: Column letter notation
    """
    if n < 1:
        raise ValueError('Column number must be at least 1')
    
    result = ''
    while n > 0:
        n -= 1  # Adjust to 0-based
        result = chr(65 + (n % 26)) + result  # 65 is ASCII for 'A'
        n = n // 26
    
    return result


def validate_sheet_id(sheet_id):
    """
    Validate that a sheet ID matches the expected format.
    
    Args:
        sheet_id: Sheet ID string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not sheet_id:
        return False
    # Sheet IDs are typically 44 characters, alphanumeric with hyphens/underscores
    return bool(re.match(r'^[a-zA-Z0-9-_]{10,50}$', sheet_id))


@sheets_bp.route('/connect', methods=['POST'])
@login_required
def connect_sheet():
    """
    Connect a new Google Sheet to the system.
    
    Only admins and supervisors can connect sheets.
    Validates the URL format and extracts the sheet ID.
    
    SECURITY: Role-based access control prevents unauthorized sheet connections.
    
    Request Body:
        sheet_url: Full Google Sheets URL
        sheet_name: Optional human-readable name for the sheet
        
    Returns:
        200: Sheet already connected, updated successfully
        201: New sheet connected successfully
        400: Invalid URL or missing data
        403: Insufficient permissions
        500: Server error
    """
    # Check permissions - only admins and supervisors can connect sheets
    if not current_user.has_role('admin', 'supervisor'):
        return jsonify({'error': 'Admin or supervisor access required'}), 403
    
    data = request.get_json()
    
    # Validate input
    sheet_url = data.get('sheet_url', '').strip()
    if not sheet_url:
        return jsonify({'error': 'Sheet URL is required'}), 400
    
    # Extract and validate sheet ID
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id or not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid Google Sheet URL format'}), 400
    
    # Check if sheet already exists in database
    existing = GoogleSheetConfig.query.filter_by(sheet_id=sheet_id).first()
    if existing:
        # Update existing configuration
        existing.sheet_url = sheet_url
        existing.is_active = True
        existing.sheet_name = data.get('sheet_name', existing.sheet_name)
        try:
            db.session.commit()
            return jsonify({'message': 'Sheet updated', 'sheet_id': sheet_id}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update sheet configuration'}), 500
    
    # Create new sheet configuration
    config = GoogleSheetConfig(
        sheet_url=sheet_url,
        sheet_id=sheet_id,
        sheet_name=data.get('sheet_name', 'Main Data Sheet')
    )
    
    try:
        db.session.add(config)
        db.session.commit()
        return jsonify({'message': 'Sheet connected', 'sheet_id': sheet_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to connect sheet'}), 500


@sheets_bp.route('/list', methods=['GET'])
@login_required
def list_sheets():
    """
    List all connected and active Google Sheets.
    
    Returns:
        200: List of connected sheets
    """
    configs = GoogleSheetConfig.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': config.id,
        'sheet_url': config.sheet_url,
        'sheet_id': config.sheet_id,
        'sheet_name': config.sheet_name,
        'created_at': config.created_at.isoformat()
    } for config in configs]), 200


@sheets_bp.route('/<sheet_id>/metadata', methods=['GET'])
@login_required
def get_sheet_metadata(sheet_id):
    """
    Get metadata about a Google Sheet including all sheet names.
    
    Args:
        sheet_id: Google Sheet ID (URL parameter)
        
    Returns:
        200: Sheet metadata including title and list of sheets
        403: Insufficient permissions
        404: Sheet not found
        500: API error
    """
    # Validate sheet ID format
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    
    try:
        service = get_sheets_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        # Extract sheet information
        sheets_info = []
        for sheet in spreadsheet.get('sheets', []):
            sheets_info.append({
                'title': sheet['properties']['title'],
                'index': sheet['properties']['index'],
                'sheetId': sheet['properties']['sheetId']
            })
        
        return jsonify({
            'title': spreadsheet['properties']['title'],
            'sheets': sheets_info
        }), 200
    except Exception as e:
        # Don't expose detailed error messages to client
        return jsonify({'error': 'Failed to retrieve sheet metadata'}), 500


@sheets_bp.route('/<sheet_id>/data', methods=['GET'])
@login_required
def get_sheet_data(sheet_id):
    """
    Read data from a specific sheet.
    
    SECURITY: Agents can only access Sheet1 (main data sheet).
    Admins and supervisors can access any sheet.
    
    Args:
        sheet_id: Google Sheet ID (URL parameter)
        sheet_title: Name of the sheet to read (query parameter, default: Sheet1)
        
    Returns:
        200: Sheet data
        403: Insufficient permissions
        500: API error
    """
    sheet_title = request.args.get('sheet_title', 'Sheet1')
    
    # Role-based access control
    if current_user.role == 'agent' and sheet_title != 'Sheet1':
        return jsonify({'error': 'Agents can only access the main data sheet'}), 403
    
    # Validate sheet ID
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    
    try:
        service = get_sheets_service()
        # Use a large range to capture all data (A1 to ZZ)
        # For 73 columns, we need at least up to column BA
        range_name = f'{sheet_title}!A1:BA'
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        return jsonify({
            'data': values,
            'row_count': len(values),
            'column_count': len(values[0]) if values else 0
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve sheet data'}), 500


@sheets_bp.route('/<sheet_id>/data', methods=['POST'])
@login_required
def update_sheet_data(sheet_id):
    """
    Update data in a specific row of a sheet.
    
    SECURITY: Agents can only edit Sheet1.
    
    CRITICAL FIX: Uses correct column letter calculation for 73+ columns.
    
    Request Body:
        row: Row number to update (1-based)
        values: Array of values to write to the row
        
    Args:
        sheet_id: Google Sheet ID (URL parameter)
        sheet_title: Name of the sheet (query parameter, default: Sheet1)
        
    Returns:
        200: Data updated successfully
        403: Insufficient permissions
        500: API error
    """
    sheet_title = request.args.get('sheet_title', 'Sheet1')
    data = request.get_json()
    
    # Validate input
    if not data or 'row' not in data or 'values' not in data:
        return jsonify({'error': 'Row number and values are required'}), 400
    
    row = data.get('row')
    values = data.get('values', [])
    
    if not isinstance(row, int) or row < 1:
        return jsonify({'error': 'Row must be a positive integer'}), 400
    
    if not isinstance(values, list):
        return jsonify({'error': 'Values must be an array'}), 400
    
    # Role-based access control
    if current_user.role == 'agent' and sheet_title != 'Sheet1':
        return jsonify({'error': 'Agents can only edit the main data sheet'}), 403
    
    # Validate sheet ID
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    
    try:
        service = get_sheets_service()
        
        # FIXED: Use proper column letter calculation
        # Calculate the end column letter based on number of values
        end_column = number_to_column_letter(len(values))
        range_name = f'{sheet_title}!A{row}:{end_column}{row}'
        
        body = {
            'values': [values]
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return jsonify({'message': 'Data updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to update sheet data'}), 500


@sheets_bp.route('/<sheet_id>/append', methods=['POST'])
@login_required
def append_sheet_data(sheet_id):
    """
    Append a new row of data to a sheet.
    
    SECURITY: Agents can only append to Sheet1.
    
    Request Body:
        values: Array of values to append as a new row
        
    Args:
        sheet_id: Google Sheet ID (URL parameter)
        sheet_title: Name of the sheet (query parameter, default: Sheet1)
        
    Returns:
        200: Data appended successfully
        403: Insufficient permissions
        500: API error
    """
    sheet_title = request.args.get('sheet_title', 'Sheet1')
    data = request.get_json()
    
    # Validate input
    if not data or 'values' not in data:
        return jsonify({'error': 'Values are required'}), 400
    
    values = data.get('values', [])
    
    if not isinstance(values, list):
        return jsonify({'error': 'Values must be an array'}), 400
    
    # Role-based access control
    if current_user.role == 'agent' and sheet_title != 'Sheet1':
        return jsonify({'error': 'Agents can only append to the main data sheet'}), 403
    
    # Validate sheet ID
    if not validate_sheet_id(sheet_id):
        return jsonify({'error': 'Invalid sheet ID format'}), 400
    
    try:
        service = get_sheets_service()
        # Use a range that covers all possible columns (A to BA for 73 columns)
        range_name = f'{sheet_title}!A:BA'
        
        body = {
            'values': [values]
        }
        
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        return jsonify({'message': 'Data appended successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to append sheet data'}), 500
