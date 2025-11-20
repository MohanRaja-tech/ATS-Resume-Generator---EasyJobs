from flask import Blueprint, request, jsonify
import pdfplumber
import docx
from io import BytesIO
import os
import sys
import tempfile
import jwt
from functools import wraps
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config

resume_bp = Blueprint('resume', __name__)

# JWT secret key from config
JWT_SECRET = Config.JWT_SECRET_KEY

# Temporary storage for extracted data
extracted_data_storage = {}

# Create extracted_texts directory if it doesn't exist
EXTRACTED_TEXTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extracted_texts')
if not os.path.exists(EXTRACTED_TEXTS_DIR):
    os.makedirs(EXTRACTED_TEXTS_DIR)

def save_extracted_text_to_file(user_id, filename, resume_text, job_description):
    """Save extracted text to a file"""
    try:
        from datetime import datetime
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean filename for safe file naming
        safe_filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        # Create output filename
        output_filename = f"extracted_text_user{user_id}_{timestamp}_{safe_filename}.txt"
        output_path = os.path.join(EXTRACTED_TEXTS_DIR, output_filename)
        
        # Prepare content
        content = f"""EXTRACTED RESUME TEXT
{'='*50}
Original Filename: {filename}
User ID: {user_id}
Extraction Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

RESUME TEXT:
{'-'*30}
{resume_text}

{'='*50}
JOB DESCRIPTION:
{'-'*30}
{job_description}

{'='*50}
Extraction completed successfully!
Total characters extracted: {len(resume_text)}
"""
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Extracted text saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error saving extracted text to file: {str(e)}")
        return None

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

def extract_text_from_pdf(file_content):
    """Extract text from PDF using pdfplumber"""
    try:
        extracted_text = []
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
        
        full_text = '\n'.join(extracted_text)
        return full_text.strip()
    
    except Exception as e:
        print(f"Error extracting PDF text: {str(e)}")
        return None

def extract_text_from_docx(file_content):
    """Extract text from DOCX using python-docx"""
    try:
        # Save content to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            
            # Extract text from docx
            doc = docx.Document(tmp_file.name)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            full_text = '\n'.join(text_content)
            return full_text.strip()
    
    except Exception as e:
        print(f"Error extracting DOCX text: {str(e)}")
        return None

def extract_text_from_doc(file_content):
    """Extract text from DOC files - basic implementation"""
    try:
        # For .doc files, we'll need a different approach
        # This is a placeholder - you might need to use additional libraries
        print("Warning: .doc file processing is limited. Please use .docx or .pdf format")
        return "DOC file detected. Please convert to PDF or DOCX for better text extraction."
    
    except Exception as e:
        print(f"Error processing DOC file: {str(e)}")
        return None

@resume_bp.route('/process', methods=['POST'])
@token_required
def process_resume(current_user_id):
    """Process resume file and job description"""
    try:
        print(f"\n=== RESUME PROCESSING STARTED ===")
        print(f"User ID: {current_user_id}")
        
        # Initialize extraction results
        extraction_results = {
            'user_id': current_user_id,
            'resume_text': None,
            'job_description': None,
            'file_info': None
        }
        
        # Get job description from form data
        job_description = request.form.get('jobDescription', '').strip()
        if job_description:
            extraction_results['job_description'] = job_description
            print(f"\nJob Description extracted:")
            print(f"Length: {len(job_description)} characters")
            print(f"Content preview: {job_description[:200]}...")
        else:
            print("\nNo job description provided")
        
        # Check if file was uploaded
        if 'resumeFile' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resumeFile']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file information
        filename = file.filename.lower()
        file_size = len(file.read())
        file.seek(0)  # Reset file pointer
        
        file_info = {
            'filename': file.filename,
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }
        extraction_results['file_info'] = file_info
        
        print(f"\nFile Information:")
        print(f"Filename: {file.filename}")
        print(f"Size: {file_info['size_mb']} MB")
        
        # Validate file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            return jsonify({'error': 'File size exceeds 10MB limit'}), 400
        
        # Read file content
        file_content = file.read()
        extracted_text = None
        
        # Extract text based on file type
        if filename.endswith('.pdf'):
            print("Processing PDF file...")
            extracted_text = extract_text_from_pdf(file_content)
            
        elif filename.endswith('.docx'):
            print("Processing DOCX file...")
            extracted_text = extract_text_from_docx(file_content)
            
        elif filename.endswith('.doc'):
            print("Processing DOC file...")
            extracted_text = extract_text_from_doc(file_content)
            
        else:
            return jsonify({'error': 'Unsupported file format. Please use PDF, DOC, or DOCX'}), 400
        
        if extracted_text:
            extraction_results['resume_text'] = extracted_text
            print(f"\nResume Text Extraction Successful:")
            print(f"Total characters: {len(extracted_text)}")
            print(f"Total words: {len(extracted_text.split())}")
            print(f"First 300 characters:")
            print(f"{extracted_text[:300]}...")
            
            # Store in temporary storage
            extracted_data_storage[current_user_id] = extraction_results
            
            # Save extracted text to file
            save_extracted_text_to_file(current_user_id, file.filename, extracted_text, job_description)
            
            print(f"\nData stored in temporary storage for user: {current_user_id}")
            print(f"Storage keys: {list(extracted_data_storage.keys())}")
            
        else:
            print("Failed to extract text from file")
            return jsonify({'error': 'Failed to extract text from file'}), 400
        
        print(f"\n=== RESUME PROCESSING COMPLETED ===\n")
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Resume and job description processed successfully',
            'data': {
                'resume_text_length': len(extracted_text) if extracted_text else 0,
                'job_description_length': len(job_description) if job_description else 0,
                'file_info': file_info
            }
        }), 200
        
    except Exception as e:
        print(f"\nError processing resume: {str(e)}")
        return jsonify({'error': f'Failed to process resume: {str(e)}'}), 500

@resume_bp.route('/get-extracted-data', methods=['GET'])
@token_required
def get_extracted_data(current_user_id):
    """Get extracted data from temporary storage"""
    try:
        if current_user_id in extracted_data_storage:
            data = extracted_data_storage[current_user_id]
            return jsonify({
                'success': True,
                'data': data
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No extracted data found for user'
            }), 404
            
    except Exception as e:
        print(f"Error retrieving extracted data: {str(e)}")
        return jsonify({'error': 'Failed to retrieve data'}), 500

@resume_bp.route('/download-extracted-text/<filename>', methods=['GET'])
def download_extracted_text(filename):
    """Download extracted text file"""
    try:
        file_path = os.path.join(EXTRACTED_TEXTS_DIR, filename)
        if os.path.exists(file_path):
            from flask import send_file
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500

@resume_bp.route('/list-extracted-files', methods=['GET'])
def list_extracted_files():
    """List all extracted text files"""
    try:
        files = []
        if os.path.exists(EXTRACTED_TEXTS_DIR):
            for filename in os.listdir(EXTRACTED_TEXTS_DIR):
                if filename.endswith('.txt'):
                    file_path = os.path.join(EXTRACTED_TEXTS_DIR, filename)
                    file_stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'modified': file_stat.st_mtime
                    })
        
        return jsonify({
            'success': True,
            'files': files,
            'total_files': len(files)
        }), 200
        
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return jsonify({'error': 'Failed to list files'}), 500

@resume_bp.route('/clear-extracted-data', methods=['DELETE'])
@token_required  
def clear_extracted_data(current_user_id):
    """Clear extracted data from temporary storage"""
    try:
        if current_user_id in extracted_data_storage:
            del extracted_data_storage[current_user_id]
            print(f"Cleared extracted data for user: {current_user_id}")
            
        return jsonify({
            'success': True,
            'message': 'Extracted data cleared successfully'
        }), 200
        
    except Exception as e:
        print(f"Error clearing extracted data: {str(e)}")
        return jsonify({'error': 'Failed to clear data'}), 500