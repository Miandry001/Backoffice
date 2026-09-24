"""
WSGI entry point for production deployment.

This file is used by Gunicorn to serve the Flask application.
"""

from backend.app import app

if __name__ == "__main__":
    app.run()
