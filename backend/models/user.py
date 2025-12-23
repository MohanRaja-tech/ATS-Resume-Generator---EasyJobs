from datetime import datetime
from bson.objectid import ObjectId
from database import Database
import bcrypt

class User:
    """User Model"""
    
    def __init__(self, email, name, password_hash, credits=3, created_at=None):
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.credits = credits
        # Welcome bonus as first purchase record
        self.credits_purchased = [{
            'amount': 3,
            'timestamp': datetime.utcnow(),
            'transaction_id': 'WELCOME_BONUS',
            'price': 0
        }]
        self.credits_used = 0
        self.resumes_generated = 0
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'email': self.email,
            'name': self.name,
            'credits': self.credits,
            'credits_purchased': self.credits_purchased,
            'credits_used': self.credits_used,
            'resumes_generated': self.resumes_generated,
            'created_at': self.created_at
        }
    
    def save(self):
        """Save user to database"""
        db = Database.get_db()
        user_data = self.to_dict()
        user_data['password_hash'] = self.password_hash
        
        result = db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    
    @staticmethod
    def _get_total_credits_purchased(credits_purchased_data):
        """
        Calculate total credits purchased from either old integer format or new array format.
        Handles backward compatibility with old schema.
        """
        if credits_purchased_data is None:
            return 3  # Default welcome bonus
        
        # Old format: single integer
        if isinstance(credits_purchased_data, (int, float)):
            return int(credits_purchased_data)
        
        # New format: array of purchase records
        if isinstance(credits_purchased_data, list):
            total = 0
            for record in credits_purchased_data:
                if isinstance(record, dict):
                    total += record.get('amount', 0)
                elif isinstance(record, (int, float)):
                    total += int(record)
            return total
        
        return 3  # Default fallback
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        db = Database.get_db()
        user_data = db.users.find_one({'email': email.lower()})
        
        if user_data:
            credits_purchased_raw = user_data.get('credits_purchased', 3)
            total_purchased = User._get_total_credits_purchased(credits_purchased_raw)
            
            return {
                'id': str(user_data['_id']),
                'email': user_data['email'],
                'name': user_data['name'],
                'password_hash': user_data['password_hash'],
                'credits': user_data.get('credits', 3),
                'credits_purchased': total_purchased,
                'credits_purchased_records': credits_purchased_raw if isinstance(credits_purchased_raw, list) else [],
                'credits_used': user_data.get('credits_used', 0),
                'resumes_generated': user_data.get('resumes_generated', 0),
                'created_at': user_data.get('created_at')
            }
        return None
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        db = Database.get_db()
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            
            if user_data:
                credits_purchased_raw = user_data.get('credits_purchased', 3)
                total_purchased = User._get_total_credits_purchased(credits_purchased_raw)
                
                return {
                    'id': str(user_data['_id']),
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'credits': user_data.get('credits', 3),
                    'credits_purchased': total_purchased,
                    'credits_purchased_records': credits_purchased_raw if isinstance(credits_purchased_raw, list) else [],
                    'credits_used': user_data.get('credits_used', 0),
                    'resumes_generated': user_data.get('resumes_generated', 0),
                    'created_at': user_data.get('created_at')
                }
        except Exception as e:
            print(f"Error finding user by ID: {str(e)}")
        return None
    
    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        db = Database.get_db()
        return db.users.find_one({'email': email.lower()}) is not None
    
    @staticmethod
    def get_current_credits(user_id):
        """
        Fetch latest credit values from MongoDB.
        Always use this method before credit operations to ensure fresh data.
        """
        db = Database.get_db()
        try:
            user_data = db.users.find_one(
                {'_id': ObjectId(user_id)},
                {'credits': 1, 'credits_used': 1, 'credits_purchased': 1, 'resumes_generated': 1}
            )
            
            if user_data:
                credits_purchased_raw = user_data.get('credits_purchased', 3)
                total_purchased = User._get_total_credits_purchased(credits_purchased_raw)
                
                return {
                    'credits': user_data.get('credits', 0),
                    'credits_used': user_data.get('credits_used', 0),
                    'credits_purchased': total_purchased,
                    'resumes_generated': user_data.get('resumes_generated', 0)
                }
        except Exception as e:
            print(f"Error fetching current credits: {str(e)}")
        return None
    
    @staticmethod
    def deduct_credits(user_id, cost=1):
        """
        Deduct credits from user and increment credits_used.
        Uses atomic MongoDB $inc operation for concurrent safety.
        
        Args:
            user_id: The user's ObjectId as string
            cost: Number of credits to deduct (default: 1)
            
        Returns:
            bool: True if successful, False otherwise
        """
        db = Database.get_db()
        try:
            # First check if user has enough credits
            current = User.get_current_credits(user_id)
            if not current or current['credits'] < cost:
                print(f"Insufficient credits. Available: {current['credits'] if current else 0}, Required: {cost}")
                return False
            
            # Atomic update: decrement credits, increment credits_used
            result = db.users.update_one(
                {'_id': ObjectId(user_id), 'credits': {'$gte': cost}},  # Ensure sufficient credits
                {
                    '$inc': {'credits': -cost, 'credits_used': cost}
                }
            )
            
            if result.modified_count > 0:
                print(f"[OK] Deducted {cost} credit(s) from user {user_id}")
                return True
            else:
                print(f"✗ Failed to deduct credits - insufficient balance or user not found")
                return False
                
        except Exception as e:
            print(f"Error deducting credits: {str(e)}")
            return False
    
    @staticmethod
    def deduct_credit(user_id):
        """
        Deduct one credit from user and increment credits_used.
        Legacy method - calls deduct_credits(user_id, 1) for backward compatibility.
        """
        return User.deduct_credits(user_id, 1)
    
    @staticmethod
    def add_credits(user_id, amount, transaction_id, price):
        """
        Add credits to user account after successful payment.
        Uses atomic MongoDB $inc and $push operations for concurrent safety.
        
        Args:
            user_id: The user's ObjectId as string
            amount: Number of credits to add
            transaction_id: Payment transaction ID
            price: Amount paid for credits
            
        Returns:
            dict: Updated credit info if successful, None otherwise
        """
        db = Database.get_db()
        try:
            # Create purchase record
            purchase_record = {
                'amount': amount,
                'timestamp': datetime.utcnow(),
                'transaction_id': transaction_id,
                'price': price      
            }
            
            # Check if credits_purchased is already an array or needs migration
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if not user_data:
                print(f"User not found: {user_id}")
                return None
            
            credits_purchased_raw = user_data.get('credits_purchased')
            
            # If old integer format, migrate to array first
            if isinstance(credits_purchased_raw, (int, float)) or credits_purchased_raw is None:
                old_value = int(credits_purchased_raw) if credits_purchased_raw else 3
                migration_record = {
                    'amount': old_value,
                    'timestamp': user_data.get('created_at', datetime.utcnow()),
                    'transaction_id': 'MIGRATED_LEGACY',
                    'price': 0
                }
                # Initialize array with migrated record
                db.users.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': {'credits_purchased': [migration_record]}}
                )
            
            # Atomic update: increment credits and push purchase record
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {
                    '$inc': {'credits': amount},
                    '$push': {'credits_purchased': purchase_record}
                }
            )
            
            if result.modified_count > 0:
                print(f"[OK] Added {amount} credit(s) to user {user_id} (Transaction: {transaction_id})")
                return User.get_current_credits(user_id)
            else:
                print(f"✗ Failed to add credits to user {user_id}")
                return None
                
        except Exception as e:
            print(f"Error adding credits: {str(e)}")
            return None
    
    @staticmethod
    def increment_resumes_generated(user_id):
        """
        Increment the resumes_generated counter by 1.
        Uses atomic MongoDB $inc operation for concurrent safety.
        
        Args:
            user_id: The user's ObjectId as string
            
        Returns:
            bool: True if successful, False otherwise
        """
        db = Database.get_db()
        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'resumes_generated': 1}}
            )
            
            if result.modified_count > 0:
                print(f"[OK] Incremented resumes_generated for user {user_id}")
                return True
            else:
                print(f"✗ Failed to increment resumes_generated")
                return False
                
        except Exception as e:
            print(f"Error incrementing resumes_generated: {str(e)}")
            return False
