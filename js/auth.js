// Authentication JavaScript
// Handles login and registration functionality

// API Configuration - Use relative URLs since Flask serves everything
const API_BASE_URL = '/api';

// Utility function to show alerts
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert alert-${type} show`;
    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

// Utility function to show/hide loading overlay
function toggleLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

// Email validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Login Form Handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        
        // Validation
        let isValid = true;
        
        if (!validateEmail(email)) {
            document.getElementById('email').classList.add('error');
            document.getElementById('emailError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('email').classList.remove('error');
            document.getElementById('emailError').classList.remove('show');
        }
        
        if (password.length < 6) {
            document.getElementById('password').classList.add('error');
            document.getElementById('passwordError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('password').classList.remove('error');
            document.getElementById('passwordError').classList.remove('show');
        }
        
        if (!isValid) return;
        
        // Show loading
        toggleLoading(true);
        
        // Make API call to backend
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            toggleLoading(false);
            
            if (data.success) {
                // Store token and user data
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userData', JSON.stringify(data.user));
                localStorage.setItem('isLoggedIn', 'true');
                
                showAlert('Login successful! Redirecting...', 'success');
                
                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1000);
            } else {
                showAlert(data.error || 'Login failed. Please try again.', 'error');
            }
        } catch (error) {
            toggleLoading(false);
            console.error('Login error:', error);
            showAlert('Connection error. Please check if the server is running.', 'error');
        }
    });
}

// Registration Form Handler
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fullName = document.getElementById('fullName').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validation
        let isValid = true;
        
        if (fullName.length < 2) {
            document.getElementById('fullName').classList.add('error');
            document.getElementById('fullNameError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('fullName').classList.remove('error');
            document.getElementById('fullNameError').classList.remove('show');
        }
        
        if (!validateEmail(email)) {
            document.getElementById('email').classList.add('error');
            document.getElementById('emailError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('email').classList.remove('error');
            document.getElementById('emailError').classList.remove('show');
        }
        
        if (password.length < 6) {
            document.getElementById('password').classList.add('error');
            document.getElementById('passwordError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('password').classList.remove('error');
            document.getElementById('passwordError').classList.remove('show');
        }
        
        if (password !== confirmPassword) {
            document.getElementById('confirmPassword').classList.add('error');
            document.getElementById('confirmPasswordError').classList.add('show');
            isValid = false;
        } else {
            document.getElementById('confirmPassword').classList.remove('error');
            document.getElementById('confirmPasswordError').classList.remove('show');
        }
        
        if (!isValid) return;
        
        // Show loading
        toggleLoading(true);
        
        // Make API call to backend
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: fullName,
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            toggleLoading(false);
            
            if (data.success) {
                // Store token and user data
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userData', JSON.stringify(data.user));
                localStorage.setItem('isLoggedIn', 'true');
                
                showAlert('Account created successfully! Redirecting...', 'success');
                
                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1000);
            } else {
                const errorMessage = data.error || (data.errors ? data.errors.join(', ') : 'Registration failed');
                showAlert(errorMessage, 'error');
            }
        } catch (error) {
            toggleLoading(false);
            console.error('Registration error:', error);
            showAlert('Connection error. Please check if the server is running.', 'error');
        }
    });
}

// Clear error messages on input
const inputs = document.querySelectorAll('.form-control');
inputs.forEach(input => {
    input.addEventListener('input', () => {
        input.classList.remove('error');
        const errorElement = document.getElementById(`${input.id}Error`);
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    });
});
