import re
from email_validator import validate_email, EmailNotValidError

def validate_signup_data(data):
    """Validate signup request data"""
    errors = []
    
    # Check required fields
    if not data.get('name'):
        errors.append('Name is required')
    elif len(data['name'].strip()) < 2:
        errors.append('Name must be at least 2 characters')
    
    if not data.get('email'):
        errors.append('Email is required')
    else:
        # Validate email format
        try:
            validate_email(data['email'])
        except EmailNotValidError:
            errors.append('Invalid email format')
    
    if not data.get('password'):
        errors.append('Password is required')
    elif len(data['password']) < 6:
        errors.append('Password must be at least 6 characters')
    
    return errors

def validate_login_data(data):
    """Validate login request data"""
    errors = []

    
    if not data.get('email'):
        errors.append('Email is required')
    
    if not data.get('password'):
        errors.append('Password is required')
    
    return errors
