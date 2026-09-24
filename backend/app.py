"""
Flask Application Entry Point

This is the main application file that initializes the Flask app, configures
security settings, and registers all API blueprints.

SECURITY IMPLEMENTATIONS:
- CORS restricted to specific frontend domain
- Rate limiting to prevent brute force attacks
- Session security flags (HTTPONLY, SAMESITE, SECURE)
- Proper error handling

BEST PRACTICES:
- Blueprint organization for modular code
- Configuration from environment variables
- Database initialization on startup
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from models import db, User
from auth import auth_bp
from admin import admin_bp
from sheets import sheets_bp
from data import data_bp

# Initialize Flask application
app = Flask(__name__)

# Load configuration from Config class (includes security settings)
app.config.from_object(Config)

# Configure CORS to only allow requests from the configured frontend URL
# This prevents unauthorized domains from accessing the API
CORS(app, resources={
    r"/api/*": {
        "origins": [Config.FRONTEND_URL],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True  # Required for session cookies
    }
})

# Initialize database with the app
db.init_app(app)

# Configure rate limiting to prevent brute force attacks
# Limits requests per IP address to protect authentication endpoints
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    strategy=Config.RATELIMIT_STRATEGY
)

# Configure Flask-Login for session-based authentication
login_manager = LoginManager()
login_manager.init_app(app)

# Retourne une erreur JSON 401 au lieu d'une redirection 404 pour l'API React
@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({
        'status': 'unauthorized',
        'message': 'Please log in to access this resource.'
    }), 401


# User loader callback - Flask-Login uses this to reload the user object
# from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database by ID.
    
    Args:
        user_id: The user's primary key ID from the session
        
    Returns:
        User object if found, None otherwise
    """
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        # Invalid user_id format
        return None

# Register API blueprints for modular route organization
# Each blueprint handles a specific domain of the application
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(sheets_bp, url_prefix='/api/sheets')
app.register_blueprint(data_bp, url_prefix='/api/data')

@app.route('/api/health', methods=['GET'])
@limiter.exempt  # Health check endpoint doesn't need rate limiting
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the current status of the API.
    
    Returns:
        JSON response with status and message
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Back office API is running',
        'version': '1.0.0'
    }), 200

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.
    Returns a consistent JSON response for missing endpoints.
    """
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.
    Returns a consistent JSON response for server errors.
    In production, log the error details for debugging.
    """
    app.logger.error(f'Server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def ratelimit_error(error):
    """
    Handle 429 Too Many Requests errors from rate limiting.
    """
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

if __name__ == '__main__':
    """
    Application entry point when run directly.
    Creates database tables if they don't exist and starts the development server.
    
    NOTE: In production, use a WSGI server like Gunicorn or uWSGI instead of
    the Flask development server.
    """
    with app.app_context():
        # Create all database tables defined in models.py
        # This is safe to run multiple times as it only creates missing tables
        db.create_all()
    
    # Start the development server
    # debug=True provides detailed error messages (disable in production)
    app.run(debug=True, port=5000, host='0.0.0.0')
