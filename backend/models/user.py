from datetime import datetime
from bson.objectid import ObjectId
from database import Database
import bcrypt

class User:
    """User Model"""
    
    def __init__(self, email, name, password_hash, credits=5, created_at=None):
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.credits = credits
        self.credits_purchased = 5  # Welcome bonus
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
    def find_by_email(email):
        """Find user by email"""
        db = Database.get_db()
        user_data = db.users.find_one({'email': email.lower()})
        
        if user_data:
            return {
                'id': str(user_data['_id']),
                'email': user_data['email'],
                'name': user_data['name'],
                'password_hash': user_data['password_hash'],
                'credits': user_data.get('credits', 5),
                'credits_purchased': user_data.get('credits_purchased', 5),
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
                return {
                    'id': str(user_data['_id']),
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'credits': user_data.get('credits', 5),
                    'credits_purchased': user_data.get('credits_purchased', 5),
                    'credits_used': user_data.get('credits_used', 0),
                    'resumes_generated': user_data.get('resumes_generated', 0),
                    'created_at': user_data.get('created_at')
                }
        except:
            pass
        return None
    
    @staticmethod
    def email_exists(email):
        """Check if email already exists"""
        db = Database.get_db()
        return db.users.find_one({'email': email.lower()}) is not None
