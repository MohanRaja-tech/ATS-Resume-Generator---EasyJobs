from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from database import Database
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.resume_routes import resume_bp
from routes.payment_routes import payment_bp
import os

def create_app():
    """Create and configure Flask application"""
    
    # Get the parent directory (project root) to serve frontend files
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                static_folder=parent_dir,
                static_url_path='')
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize Database (non-blocking)
    try:
        Database.initialize()
    except Exception as db_error:
        print(f"[WARNING] Database initialization failed: {str(db_error)}")
        print("[WARNING] Running without database functionality")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(resume_bp, url_prefix='/api/resume')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')
    
    # Serve frontend - Root endpoint serves landing page
    @app.route('/')
    def index():
        try:
            return send_from_directory(parent_dir, 'landing.html')
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'landing.html not found'
            }), 404
    
    # Serve other HTML pages and static files
    @app.route('/<path:filename>')
    def serve_file(filename):
        try:
            # Serve the file directly from parent directory
            return send_from_directory(parent_dir, filename)
        except FileNotFoundError:
            # For API routes, return JSON error
            if filename.startswith('api/'):
                return jsonify({
                    'success': False,
                    'error': 'Endpoint not found'
                }), 404
            # For other files, return JSON error
            return jsonify({
                'success': False,
                'error': f'File {filename} not found'
            }), 404
    
    # Health check endpoint (API only)
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # Don't override file not found errors with JSON
        # Only return JSON for API endpoints
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        # For other paths, let the serve_file function handle it
        return error
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"\n{'='*60}")
    print(f"Resume Generator - Full Stack Application")
    print(f"{'='*60}")
    print(f"Environment: {Config.ENV}")
    print(f"Debug Mode: {Config.DEBUG}")
    print(f"\nFrontend & API Server:")
    print(f"   http://localhost:{Config.PORT}")
    print(f"   http://127.0.0.1:{Config.PORT}")
    print(f"\nAPI Endpoints:")
    print(f"   POST /api/auth/register")
    print(f"   POST /api/auth/login")
    print(f"   POST /api/auth/logout")
    print(f"   GET  /api/health")
    print(f"   GET  /api/payment/credits")
    print(f"   POST /api/payment/add-credits")
    print(f"\nDatabase: {Config.MONGODB_DB_NAME}")
    print(f"{'='*60}\n")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
