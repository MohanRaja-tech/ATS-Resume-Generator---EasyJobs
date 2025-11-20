from flask import Blueprint, request, jsonify
from models.user import User
from utils.auth import generate_token
from utils.validators import validate_signup_data, validate_login_data

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        # Validate input data
        errors = validate_signup_data(data)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Check if user already exists
        if User.email_exists(email):
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 409
        
        # Hash password
        password_hash = User.hash_password(password)
        
        # Create new user
        user = User(
            email=email,
            name=name,
            password_hash=password_hash
        )
        
        # Save to database
        user_id = user.save()
        
        # Generate JWT token
        token = generate_token(user_id, email)
        
        # Get user data
        user_data = User.find_by_id(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'token': token,
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'email': user_data['email'],
                'credits': user_data['credits'],
                'credits_purchased': user_data['credits_purchased'],
                'credits_used': user_data['credits_used'],
                'resumes_generated': user_data['resumes_generated'],
                'member_since': user_data['created_at'].strftime('%B %d, %Y') if user_data['created_at'] else None
            }
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Registration failed. Please try again.'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # Validate input data
        errors = validate_login_data(data)
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user by email
        user_data = User.find_by_email(email)
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Verify password
        if not User.verify_password(password, user_data['password_hash']):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Generate JWT token
        token = generate_token(user_data['id'], email)
        
        if not token:
            print("❌ Failed to generate token")
            return jsonify({
                'success': False,
                'error': 'Failed to generate authentication token'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user_data['id'],
                'name': user_data['name'],
                'email': user_data['email'],
                'credits': user_data['credits'],
                'credits_purchased': user_data['credits_purchased'],
                'credits_used': user_data['credits_used'],
                'resumes_generated': user_data['resumes_generated'],
                'member_since': user_data['created_at'].strftime('%B %d, %Y') if user_data['created_at'] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Login failed. Please try again.'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint (client-side token removal)"""
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200
