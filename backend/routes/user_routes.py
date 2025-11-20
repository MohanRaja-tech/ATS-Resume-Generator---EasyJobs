from flask import Blueprint, request, jsonify
from bson import ObjectId
import jwt
from functools import wraps
import os

user_bp = Blueprint('user', __name__)

# JWT secret key
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')

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
            # Decode token
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user_id = data['user_id']
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
        from models.user import User
        
        # Fetch user from database
        user = User.find_by_id(current_user_id)
        
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
