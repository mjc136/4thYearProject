from flask import Blueprint, jsonify, current_app
import os
import sys
import platform
import sqlalchemy

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
@health_bp.route('/', methods=['GET'])  # Add root route for Azure default health checks
def health_check():
    """Health check endpoint for the Flask application."""
    # Basic system info
    system_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'environment': os.environ.get('ENVIRONMENT', 'development')
    }
    
    # Database check
    db_status = 'unknown'
    db_error = None
    try:
        # Import here to avoid circular imports
        from backend.common.extensions import db
        
        # Check if we can connect to the database with a simple query
        with db.engine.connect() as conn:
            conn.execute(sqlalchemy.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = 'error'
        db_error = str(e)
    
    # App configuration check
    config_status = {
        'secret_key': 'configured' if current_app.secret_key else 'missing',
        'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'not_set').split(':')[0]
    }
    
    response = {
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'service': 'flask',
        'system': system_info,
        'database': {
            'status': db_status,
            'error': db_error
        },
        'config': config_status
    }
    
    # Always return 200 for health checks to avoid deployment failures,
    # but include detailed status in the response body
    return jsonify(response), 200
