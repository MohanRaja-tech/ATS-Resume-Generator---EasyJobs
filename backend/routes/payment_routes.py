from flask import Blueprint, request, jsonify
from bson import ObjectId
import jwt
from functools import wraps
import os
import sys
from datetime import datetime

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config

payment_bp = Blueprint('payment', __name__)

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


@payment_bp.route('/credits', methods=['GET'])
@token_required
def get_credits(current_user_id):
    """
    Get current credit information from MongoDB.
    Always fetches fresh data from database.
    """
    try:
        print(f"\n=== FETCHING CREDITS ===")
        print(f"User ID: {current_user_id}")
        
        from models.user import User
        
        # Fetch latest credits from MongoDB
        credit_info = User.get_current_credits(current_user_id)
        
        if not credit_info:
            return jsonify({
                'error': 'User not found'
            }), 404
        
        print(f"[OK] Credits fetched: {credit_info}")
        
        return jsonify({
            'success': True,
            'data': {
                'credits_available': credit_info.get('credits', 0),
                'credits_used': credit_info.get('credits_used', 0),
                'credits_purchased': credit_info.get('credits_purchased', 0),
                'resumes_generated': credit_info.get('resumes_generated', 0)
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching credits: {str(e)}")
        return jsonify({'error': 'Failed to fetch credits'}), 500


@payment_bp.route('/add-credits', methods=['POST'])
@token_required
def add_credits(current_user_id):
    """
    Add credits to user account after successful payment.
    Uses atomic MongoDB operations for concurrent safety.
    
    Expected request body:
    {
        "amount": int,           # Number of credits to add
        "transaction_id": str,   # Payment transaction ID
        "price": float           # Amount paid
    }
    """
    try:
        print(f"\n=== ADDING CREDITS ===")
        print(f"User ID: {current_user_id}")
        
        from models.user import User
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        amount = data.get('amount')
        transaction_id = data.get('transaction_id')
        price = data.get('price', 0)
        
        if not amount or not isinstance(amount, int) or amount <= 0:
            return jsonify({'error': 'Invalid credit amount'}), 400
        
        if not transaction_id:
            return jsonify({'error': 'Transaction ID is required'}), 400
        
        print(f"Adding {amount} credits for transaction: {transaction_id}")
        
        # Add credits using atomic MongoDB operation
        updated_credits = User.add_credits(
            user_id=current_user_id,
            amount=amount,
            transaction_id=transaction_id,
            price=price
        )
        
        if not updated_credits:
            return jsonify({
                'error': 'Failed to add credits. Please contact support.',
                'transaction_id': transaction_id
            }), 500
        
        print(f"[OK] Credits added successfully")
        
        return jsonify({
            'success': True,
            'message': f'Successfully added {amount} credits',
            'data': {
                'credits_added': amount,
                'credits_available': updated_credits.get('credits', 0),
                'credits_used': updated_credits.get('credits_used', 0),
                'credits_purchased': updated_credits.get('credits_purchased', 0),
                'transaction_id': transaction_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"Error adding credits: {str(e)}")
        return jsonify({
            'error': 'Failed to add credits',
            'details': str(e)
        }), 500


@payment_bp.route('/purchase-history', methods=['GET'])
@token_required
def get_purchase_history(current_user_id):
    """
    Get user's credit purchase history.
    """
    try:
        print(f"\n=== FETCHING PURCHASE HISTORY ===")
        print(f"User ID: {current_user_id}")
        
        from models.user import User
        from database import Database
        from bson.objectid import ObjectId
        
        db = Database.get_db()
        user_data = db.users.find_one(
            {'_id': ObjectId(current_user_id)},
            {'credits_purchased': 1}
        )
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        credits_purchased_raw = user_data.get('credits_purchased', [])
        
        # Handle old integer format
        if isinstance(credits_purchased_raw, (int, float)):
            purchases = [{
                'amount': int(credits_purchased_raw),
                'timestamp': None,
                'transaction_id': 'LEGACY',
                'price': 0
            }]
        elif isinstance(credits_purchased_raw, list):
            purchases = []
            for record in credits_purchased_raw:
                if isinstance(record, dict):
                    purchases.append({
                        'amount': record.get('amount', 0),
                        'timestamp': record.get('timestamp').isoformat() if record.get('timestamp') else None,
                        'transaction_id': record.get('transaction_id', 'UNKNOWN'),
                        'price': record.get('price', 0)
                    })
        else:
            purchases = []
        
        # Sort by timestamp (most recent first)
        purchases.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'purchases': purchases,
                'total_purchases': len(purchases)
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching purchase history: {str(e)}")
        return jsonify({'error': 'Failed to fetch purchase history'}), 500
