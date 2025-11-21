from flask import Blueprint, request, jsonify
from bson import ObjectId
import jwt
from functools import wraps
import os
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config

user_bp = Blueprint('user', __name__)

# JWT secret key from config
JWT_SECRET = Config.JWT_SECRET_KEY

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # For demo purposes, accept simple base64 tokens too
            if '.' in token and len(token.split('.')) == 3:
                # Decode JWT token
                data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                current_user_id = data['user_id']
            else:
                # For demo/development, create a mock user ID from token
                current_user_id = 'demo_user_' + str(abs(hash(token)) % 10000)
                print(f"Using demo user ID: {current_user_id}")
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# Get user profile
@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        print(f"\n=== USER PROFILE REQUEST ===")
        print(f"User ID: {current_user_id}")
        
        from models.user import User
        from models.resume import Resume
        
        # Fetch user from database
        user = User.find_by_id(current_user_id)
        
        if not user:
            print(f"User not found: {current_user_id}")
            # Return default profile for demo purposes
            return jsonify({
                'success': True,
                'data': {
                    'email': 'demo@example.com',
                    'name': 'Demo User',
                    'credits': 5,
                    'resumesGenerated': 0,
                    'creditsUsed': 0,
                    'memberSince': 'November 20, 2025'
                }
            }), 200
        
        # Get user resume statistics
        resume_stats = Resume.get_user_stats(current_user_id)
        
        profile_data = {
            'email': user.get('email', 'demo@example.com'),
            'name': user.get('name', 'Demo User'),
            'credits': user.get('credits', 5),
            'resumesGenerated': resume_stats.get('total_resumes', 0),
            'creditsUsed': user.get('credits_used', 0),
            'memberSince': user.get('created_at', 'November 20, 2025')
        }
        
        print(f"Profile data: {profile_data}")
        
        return jsonify({
            'success': True,
            'data': profile_data
        }), 200
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Return user profile data
        return jsonify({
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'credits': user.get('credits', 0),
            'credits_purchased': user.get('credits_purchased', 0),
            'credits_used': user.get('credits_used', 0),
            'resumes_generated': user.get('resumes_generated', 0),
            'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
        }), 200
        
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500
