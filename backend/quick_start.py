#!/usr/bin/env python3
"""
Quick server startup script that handles MongoDB connection gracefully
"""

import os
import sys
from flask import Flask, jsonify

# Add the backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def create_simple_app():
    """Create Flask app with graceful MongoDB handling"""
    
    # Import after path setup
    from config import Config
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp  
    from routes.resume_routes import resume_bp
    from flask_cors import CORS
    
    # Create Flask app
    parent_dir = os.path.dirname(backend_dir)
    app = Flask(__name__, static_folder=parent_dir, static_url_path='')
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["*"],  # Allow all origins for development
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Initialize Database with error handling
    try:
        from database import Database
        Database.initialize()
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {str(e)}")
        print("⚠️  Running in demo mode without database")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(resume_bp, url_prefix='/api/resume')
    
    # Health check endpoint
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy', 'service': 'resume_generator'})
    
    # Serve frontend files
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    return app

if __name__ == '__main__':
    app = create_simple_app()
    
    print("\n" + "="*60)
    print("🚀 Resume Generator - Quick Start")
    print("="*60)
    print(f"🌐 Server: http://localhost:5000")
    print(f"🌐 Dashboard: http://localhost:5000/dashboard.html")
    print(f"🌐 Profile: http://localhost:5000/profile.html")
    print("="*60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to prevent MongoDB connection issues
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {str(e)}")
        print("💡 Try running: pip install -r requirements.txt")