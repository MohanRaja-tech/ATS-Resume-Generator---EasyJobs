from flask import Blueprint, request, jsonify, send_file, Response, Response
import pdfplumber
import docx
from io import BytesIO
import os
import sys
import tempfile
import jwt
from functools import wraps
import requests
import base64
import json
import re
import time
import binascii
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config
from models.resume import Resume
import binascii

resume_bp = Blueprint('resume', __name__)

# JWT secret key from config
JWT_SECRET = Config.JWT_SECRET_KEY

# Temporary storage for extracted data - now includes text directly
extracted_data_storage = {}

def clean_text_for_latex(text):
    """
    Clean extracted text to make it compatible with LaTeX compilation.
    
    Args:
        text: Raw extracted text from PDF
        
    Returns:
        Cleaned text safe for LaTeX processing
    """
    if not text:
        return text
    
    # Remove or replace problematic characters
    text = text.replace('\\', '')  # Remove backslashes
    text = text.replace('{', '(')   # Replace curly braces
    text = text.replace('}', ')')
    text = text.replace('$', 'USD')  # Replace dollar signs
    text = text.replace('#', 'No.')  # Replace hash symbols
    text = text.replace('%', ' percent')  # Replace percentage signs
    text = text.replace('&', ' and ')  # Replace ampersands
    text = text.replace('_', ' ')    # Replace underscores
    text = text.replace('^', '')     # Remove carets
    text = text.replace('~', '')     # Remove tildes
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
    
    # Remove non-ASCII characters that might cause issues
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    print(f"Text cleaned: {len(text)} characters after cleaning")
    return text

def send_to_aws_api(resume_text, job_description, api_url):
    """
    Send extracted text to AWS hosted API and get base64 PDF response.
    
    Args:
        resume_text: Extracted text from PDF
        job_description: Job description text
        api_url: AWS API endpoint URL
        
    Returns:
        Base64 encoded PDF data from API
    """
    try:
        # Clean the resume text for LaTeX compatibility
        cleaned_resume_text = clean_text_for_latex(resume_text)
        
        # Prepare the payload matching the API structure
        payload = {
            "resume_data": cleaned_resume_text,
            "job_description": job_description if job_description else ""
        }
        
        print("\nSending request to AWS API...")
        print(f"Payload size: {len(json.dumps(payload))} bytes")
        
        # Record start time
        start_time = time.time()
        
        # Send POST request to API with timeout
        response = requests.post(api_url, json=payload, timeout=60)
        
        # Calculate time taken
        end_time = time.time()
        time_taken = end_time - start_time
        
        print(f"Response received in {time_taken:.2f} seconds")
        print(f"HTTP Status Code: {response.status_code}")
        
        # Check if request was successful
        if response.status_code == 200:
            try:
                # Parse JSON response
                response_data = response.json()
                
                # Extract base64 PDF data (handling different response structures)
                base64_pdf = (
                    response_data.get('pdf_base64') or 
                    response_data.get('body') or 
                    response_data
                )
                
                # Ensure it's a string
                if isinstance(base64_pdf, str):
                    pdf_data = base64_pdf
                else:
                    pdf_data = str(base64_pdf)
                
                print("[OK] Successfully received base64 PDF data")
                return pdf_data
                
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON response: {str(e)}")
            except Exception as e:
                raise Exception(f"Error processing response: {str(e)}")
        else:
            # Try to parse error response for more details
            try:
                error_data = response.json()
                error_message = f"API request failed with status {response.status_code}\n"
                
                if 'error' in error_data:
                    error_message += f"Error: {error_data['error']}\n"
                    
                    # Check for LaTeX compilation errors specifically
                    if 'LaTeX compilation failed' in str(error_data.get('error', '')):
                        error_message += "\n🔧 SOLUTION SUGGESTIONS:\n"
                        error_message += "1. Your resume contains special characters that break LaTeX\n"
                        error_message += "2. Try using a simpler PDF with basic text formatting\n"
                        error_message += "3. Ensure your resume doesn't have complex tables or graphics\n"
                        error_message += "4. Check that all text is properly encoded (no special symbols)\n"
                
                error_message += f"\nFull Response: {response.text[:1000]}"
                raise Exception(error_message)
                
            except json.JSONDecodeError:
                raise Exception(
                    f"API request failed with status {response.status_code}\n"
                    f"Response: {response.text[:500]}"
                )
    
    except requests.exceptions.Timeout:
        raise Exception("Request timed out after 60 seconds")
    except requests.exceptions.ConnectionError:
        raise Exception("Failed to connect to API endpoint")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")

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
            # For demo purposes, accept simple base64 tokens too
            if '.' in token and len(token.split('.')) == 3:
                # Decode JWT token
                data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                current_user_id = data['user_id']
            else:
                # For demo/development, create a mock user ID from token
                current_user_id = 'demo_user_' + str(abs(hash(token)) % 10000)
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
            
            # Store in temporary storage with the actual text
            extracted_data_storage[current_user_id] = extraction_results
            
            # Optional: Still save to file for backup/debugging
            save_extracted_text_to_file(current_user_id, file.filename, extracted_text, job_description)
            
            print(f"\nData stored in memory storage for user: {current_user_id}")
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

@resume_bp.route('/generate-resume', methods=['POST'])
@token_required
def generate_resume(current_user_id):
    """Generate optimized resume using AWS API"""
    try:
        print(f"\n=== RESUME GENERATION STARTED ===")
        print(f"User ID: {current_user_id}")
        
        # Import User model for credit operations
        from models.user import User
        
        # Step 1: Fetch latest credits from MongoDB (NOT from memory/cache)
        credit_info = User.get_current_credits(current_user_id)
        if not credit_info:
            return jsonify({
                'error': 'User not found. Please log in again.'
            }), 404
        
        available_credits = credit_info.get('credits', 0)
        print(f"Available credits: {available_credits}")
        
        # Step 2: Check if user has sufficient credits
        if available_credits < 1:
            return jsonify({
                'error': 'Insufficient credits. Please purchase more credits to generate resumes.',
                'credits_available': available_credits
            }), 402  # Payment Required
        
        # Check if user has extracted data in storage
        if current_user_id not in extracted_data_storage:
            return jsonify({
                'error': 'No resume data found. Please upload and process a resume first.'
            }), 404
        
        user_data = extracted_data_storage[current_user_id]
        resume_text = user_data.get('resume_text')
        
        if not resume_text:
            return jsonify({
                'error': 'No resume text found. Please upload and process a resume first.'
            }), 404
        
        # Get optional job description from request
        request_data = request.get_json() if request.is_json else {}
        job_description = request_data.get('job_description', user_data.get('job_description', ''))
        
        # Get AWS API URL from environment config (NOT hardcoded)
        aws_api_url = Config.AWS_RESUME_API
        if not aws_api_url:
            print("ERROR: AWS_RESUME_API not configured in environment")
            return jsonify({
                'error': 'Resume generation service is not configured. Please contact support.'
            }), 500
        
        print(f"Using AWS API: {aws_api_url}")
        print(f"Resume text length: {len(resume_text)} characters")
        print(f"Job description length: {len(job_description) if job_description else 0} characters")
        
        # Step 3: DEDUCT CREDIT NOW (when API is about to be hit)
        deduction_success = User.deduct_credits(current_user_id, 1)
        if not deduction_success:
            return jsonify({
                'error': 'Failed to deduct credits. Please try again.',
                'credits_available': available_credits
            }), 500
        print(f"[OK] Credit deducted before API call")
        
        # Step 4: Send to AWS API
        try:
            base64_pdf_data = send_to_aws_api(resume_text, job_description, aws_api_url)
            
            # Validate base64 data
            if not base64_pdf_data:
                raise Exception("Received empty base64 data from API")
            
            # Try to decode to validate it's proper base64
            try:
                pdf_bytes = base64.b64decode(base64_pdf_data)
                pdf_size_kb = len(pdf_bytes) / 1024
                
                print(f"[OK] Generated PDF size: {pdf_size_kb:.2f} KB")
                
                # Step 5: API SUCCESS - Increment resumes_generated counter
                User.increment_resumes_generated(current_user_id)
                print(f"[OK] resumes_generated incremented")
                
                # Save resume to database
                resume = Resume(
                    user_id=current_user_id,
                    original_filename=user_data.get('file_info', {}).get('filename', 'unknown.pdf'),
                    job_description=job_description,
                    resume_text=resume_text,
                    pdf_base64=base64_pdf_data,
                    file_size_kb=round(pdf_size_kb, 2)
                )
                
                resume_id = resume.save()
                print(f" Resume saved to database with ID: {resume_id}")
                
                # Fetch updated credit info
                updated_credits = User.get_current_credits(current_user_id)
                
                # Return success response with resume ID and updated credits
                return jsonify({
                    'success': True,
                    'message': 'Resume generated successfully',
                    'data': {
                        'resume_id': resume_id,
                        'pdf_base64': base64_pdf_data,
                        'pdf_size_kb': round(pdf_size_kb, 2),
                        'resume_text_length': len(resume_text),
                        'job_description_length': len(job_description) if job_description else 0,
                        'generation_timestamp': datetime.now().isoformat(),
                        'original_filename': user_data.get('file_info', {}).get('filename', 'unknown.pdf'),
                        'credits_remaining': updated_credits.get('credits', 0) if updated_credits else 0,
                        'credits_used': updated_credits.get('credits_used', 0) if updated_credits else 0,
                        'resumes_generated': updated_credits.get('resumes_generated', 0) if updated_credits else 0
                    }
                }), 200
                
            except binascii.Error:
                raise Exception("Invalid base64 data received from API")
                
        except Exception as api_error:
            # API FAILED - Credit already deducted, resumes_generated NOT incremented
            print(f"API Error: {str(api_error)}")
            print("✗ Credit was deducted but API failed - resumes_generated NOT incremented")
            return jsonify({
                'error': f'Resume generation failed: {str(api_error)}'
            }), 500
            
    except Exception as e:
        print(f"Error generating resume: {str(e)}")
        return jsonify({
            'error': f'Failed to generate resume: {str(e)}'
        }), 500

@resume_bp.route('/download/<resume_id>', methods=['GET'])
@token_required
def download_resume(current_user_id, resume_id):
    """Download generated resume PDF"""
    try:
        print(f"\n=== RESUME DOWNLOAD STARTED ===")
        print(f"User ID: {current_user_id}")
        print(f"Resume ID: {resume_id}")
        
        # Find resume in database
        resume_doc = Resume.find_by_id(resume_id)
        
        if not resume_doc:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Check if resume belongs to current user
        if resume_doc['user_id'] != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get PDF data
        pdf_base64 = resume_doc['pdf_base64']
        if not pdf_base64:
            return jsonify({'error': 'PDF data not available'}), 404
        
        # Decode base64 to bytes
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
        except Exception as decode_error:
            return jsonify({'error': 'Failed to decode PDF data'}), 500
        
        # Update download count
        Resume.update_download_count(resume_id)
        
        # Generate filename
        timestamp = resume_doc['created_at'].strftime('%Y%m%d_%H%M%S')
        filename = f"optimized_resume_{timestamp}.pdf"
        
        print(f"[OK] Sending PDF download: {len(pdf_bytes)} bytes")
        
        # Return PDF as download
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf',
                'Content-Length': str(len(pdf_bytes))
            }
        )
        
    except Exception as e:
        print(f"Error downloading resume: {str(e)}")
        return jsonify({'error': f'Failed to download resume: {str(e)}'}), 500

@resume_bp.route('/user-resumes', methods=['GET'])
@token_required
def get_user_resumes(current_user_id):
    """Get all resumes for current user"""
    try:
        print(f"\n=== FETCHING USER RESUMES ===")
        print(f"User ID: {current_user_id}")
        
        # Get limit from query params
        limit = request.args.get('limit', type=int)
        
        # Fetch resumes from database
        resumes = Resume.find_by_user_id(current_user_id, limit=limit)
        
        # Get user stats
        stats = Resume.get_user_stats(current_user_id)
        
        print(f"[OK] Found {len(resumes)} resumes for user")
        
        return jsonify({
            'success': True,
            'data': {
                'resumes': resumes,
                'stats': stats,
                'total_count': len(resumes)
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching user resumes: {str(e)}")
        return jsonify({'error': f'Failed to fetch resumes: {str(e)}'}), 500

@resume_bp.route('/resume-details/<resume_id>', methods=['GET'])
@token_required
def get_resume_details(current_user_id, resume_id):
    """Get detailed information about a specific resume"""
    try:
        print(f"\n=== FETCHING RESUME DETAILS ===")
        print(f"User ID: {current_user_id}")
        print(f"Resume ID: {resume_id}")
        
        # Find resume in database
        resume_doc = Resume.find_by_id(resume_id)
        
        if not resume_doc:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Check if resume belongs to current user
        if resume_doc['user_id'] != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Return resume details (without PDF data for performance)
        resume_details = {
            'id': str(resume_doc['_id']),
            'original_filename': resume_doc['original_filename'],
            'job_description': resume_doc.get('job_description', ''),
            'file_size_kb': resume_doc.get('file_size_kb', 0),
            'status': resume_doc['status'],
            'created_at': resume_doc['created_at'].isoformat(),
            'download_count': resume_doc.get('download_count', 0),
            'last_downloaded': resume_doc.get('last_downloaded').isoformat() if resume_doc.get('last_downloaded') else None
        }
        
        print(f"[OK] Resume details fetched successfully")
        
        return jsonify({
            'success': True,
            'data': resume_details
        }), 200
        
    except Exception as e:
        print(f"Error fetching resume details: {str(e)}")
        return jsonify({'error': f'Failed to fetch resume details: {str(e)}'}), 500

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