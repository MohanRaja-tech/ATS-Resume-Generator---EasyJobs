from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import Config
from urllib.parse import quote_plus
import sys

class Database:
    """MongoDB Database Handler"""
    
    client = None
    db = None
    
    @staticmethod
    def initialize():
        """Initialize MongoDB connection"""
        try:
            # URL encode the username and password
            username = quote_plus("mohantwo3_db_user")
            password = quote_plus("Techiee@2k24")
            
            # Construct the properly encoded MongoDB URI
            mongo_uri = f"mongodb+srv://{username}:{password}@cluster0.2beejft.mongodb.net/"
            
            Database.client = MongoClient(mongo_uri)
            
            # Test connection
            Database.client.admin.command('ping')
            
            Database.db = Database.client[Config.MONGODB_DATABASE]
            
            # Create indexes
            Database.db.users.create_index('email', unique=True)
            
            print(f"✓ Connected to MongoDB: {Config.MONGODB_DATABASE}")
            return True
            
        except ConnectionFailure as e:
            print(f"✗ MongoDB connection failed: {str(e)}")
            print("⚠️  The application will run with limited functionality")
            Database.client = None
            Database.db = None
            return False
        except Exception as e:
            print(f"✗ Database initialization error: {str(e)}")
            print("⚠️  The application will run with limited functionality")
            Database.client = None
            Database.db = None
            return False
    
    @staticmethod
    def get_db():
        """Get database instance"""
        if Database.db is None:
            Database.initialize()
        return Database.db
    
    @staticmethod
    def close():
        """Close database connection"""
        if Database.client:
            Database.client.close()
            print("✓ MongoDB connection closed")
