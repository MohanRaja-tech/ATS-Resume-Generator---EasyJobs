from datetime import datetime
from bson.objectid import ObjectId
from database import Database

class Resume:
    """Resume Model for storing generated resumes"""
    
    def __init__(self, user_id, original_filename, job_description, resume_text, 
                 pdf_base64, file_size_kb, created_at=None):
        self.user_id = user_id
        self.original_filename = original_filename
        self.job_description = job_description
        self.resume_text = resume_text
        self.pdf_base64 = pdf_base64
        self.file_size_kb = file_size_kb
        self.status = 'completed'
        self.created_at = created_at or datetime.utcnow()
        self.download_count = 0
        self.last_downloaded = None
    
    def to_dict(self):
        """Convert resume object to dictionary"""
        return {
            'user_id': self.user_id,
            'original_filename': self.original_filename,
            'job_description': self.job_description,
            'resume_text': self.resume_text,
            'pdf_base64': self.pdf_base64,
            'file_size_kb': self.file_size_kb,
            'status': self.status,
            'created_at': self.created_at,
            'download_count': self.download_count,
            'last_downloaded': self.last_downloaded
        }
    
    def save(self):
        """Save resume to database"""
        try:
            db = Database.get_db()
            if db is None:
                print("[WARNING] Database not available - resume not saved to database")
                return None
                
            resume_data = self.to_dict()
            result = db.resumes.insert_one(resume_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Error saving resume to database: {str(e)}")
            return None
    
    @staticmethod
    def find_by_user_id(user_id, limit=None):
        """Find resumes by user ID"""
        try:
            db = Database.get_db()
            if db is None:
                return []
                
            query = {'user_id': user_id}
            cursor = db.resumes.find(query).sort('created_at', -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            resumes = []
            for resume_doc in cursor:
                # Convert to resume-like dict for frontend
                resume_dict = {
                    'id': str(resume_doc['_id']),
                    'date': resume_doc['created_at'].strftime('%Y-%m-%d'),
                    'originalFile': resume_doc['original_filename'],
                    'jobDesc': 'Provided' if resume_doc.get('job_description') else 'None',
                    'status': resume_doc['status'].title(),
                    'file_size_kb': resume_doc.get('file_size_kb', 0),
                    'download_count': resume_doc.get('download_count', 0),
                    'created_at': resume_doc['created_at']
                }
                resumes.append(resume_dict)
            
            return resumes
        except Exception as e:
            print(f"❌ Error fetching user resumes: {str(e)}")
            return []
    
    @staticmethod
    def find_by_id(resume_id):
        """Find resume by ID"""
        try:
            db = Database.get_db()
            if db is None:
                return None
                
            resume_doc = db.resumes.find_one({'_id': ObjectId(resume_id)})
            return resume_doc
        except Exception as e:
            print(f"❌ Error fetching resume by ID: {str(e)}")
            return None
    
    @staticmethod
    def update_download_count(resume_id):
        """Update download count and last downloaded timestamp"""
        try:
            db = Database.get_db()
            if db is None:
                return False
                
            result = db.resumes.update_one(
                {'_id': ObjectId(resume_id)},
                {
                    '$inc': {'download_count': 1},
                    '$set': {'last_downloaded': datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Error updating download count: {str(e)}")
            return False
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user resume statistics"""
        try:
            db = Database.get_db()
            if db is None:
                return {'total_resumes': 0, 'total_downloads': 0}
                
            pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {
                    '_id': None,
                    'total_resumes': {'$sum': 1},
                    'total_downloads': {'$sum': '$download_count'}
                }}
            ]
            
            result = list(db.resumes.aggregate(pipeline))
            if result:
                return {
                    'total_resumes': result[0]['total_resumes'],
                    'total_downloads': result[0]['total_downloads']
                }
            return {'total_resumes': 0, 'total_downloads': 0}
        except Exception as e:
            print(f"❌ Error fetching user stats: {str(e)}")
            return {'total_resumes': 0, 'total_downloads': 0}