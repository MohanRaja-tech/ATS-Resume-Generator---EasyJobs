// Dashboard JavaScript
// Handles file uploads, resume generation, and dashboard functionality

// Check authentication
function checkAuth() {
    try {
        const isLoggedIn = localStorage.getItem('isLoggedIn');
        const authToken = localStorage.getItem('authToken');
        
        console.log('🔍 Auth Check:', { isLoggedIn, hasToken: !!authToken });
        
        if (!isLoggedIn || isLoggedIn !== 'true' || !authToken) {
            console.log('❌ Authentication failed - redirecting to login');
            window.location.href = 'index.html';
            return false;
        }
        
        // Validate token format
        if (!authToken.includes('.')) {
            console.log('❌ Invalid token format - clearing auth');
            localStorage.removeItem('authToken');
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userData');
            window.location.href = 'index.html';
            return false;
        }
        
        // Set demo data if not exists (for migration from old system)
        if (!localStorage.getItem('userData')) {
            const demoUserData = {
                email: 'demo@easyjobs.com',
                name: 'Demo User',
                credits: 5,
                resumesGenerated: 0,
                creditsUsed: 0,
                memberSince: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
            };
            localStorage.setItem('userData', JSON.stringify(demoUserData));
        }
        
        console.log('✅ Authentication validated');
        return true;
    } catch (error) {
        console.error('❌ Auth check error:', error);
        window.location.href = 'index.html';
        return false;
    }
}

// Initialize dashboard
checkAuth();

// Load user data
function loadUserData() {
    try {
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        
        // Safety checks for DOM elements
        const userNameEl = document.getElementById('userName');
        const creditsRemainingEl = document.getElementById('creditsRemaining');
        const resumesGeneratedEl = document.getElementById('resumesGenerated');
        const creditsUsedEl = document.getElementById('creditsUsed');
        
        if (userNameEl) userNameEl.textContent = userData.name || 'User';
        if (creditsRemainingEl) creditsRemainingEl.textContent = userData.credits || 0;
        if (resumesGeneratedEl) resumesGeneratedEl.textContent = userData.resumesGenerated || 0;
        if (creditsUsedEl) creditsUsedEl.textContent = userData.creditsUsed || 0;
        
        // Load resume history
        loadResumeHistory();
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Utility functions
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert alert-${type} show`;
    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

function toggleLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

// File upload handlers
let resumeFile = null;

// Resume file upload
const resumeFileInput = document.getElementById('resumeFile');
const resumeUploadArea = document.getElementById('resumeUploadArea');

resumeFileInput.addEventListener('change', (e) => {
    handleResumeFile(e.target.files[0]);
});

// Drag and drop for resume
resumeUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    resumeUploadArea.classList.add('dragover');
});

resumeUploadArea.addEventListener('dragleave', () => {
    resumeUploadArea.classList.remove('dragover');
});

resumeUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    resumeUploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        handleResumeFile(e.dataTransfer.files[0]);
    }
});

resumeUploadArea.addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') {
        resumeFileInput.click();
    }
});

function handleResumeFile(file) {
    if (!file) return;
    
    // Validate file type
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
        showAlert('Please upload a PDF or Word document', 'error');
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showAlert('File size must be less than 10MB', 'error');
        return;
    }
    
    resumeFile = file;
    document.getElementById('resumeFileName').textContent = file.name;
    
    // Update file icon based on file type
    const fileIcon = document.querySelector('#resumeFileInfo .file-icon');
    if (file.type.includes('pdf')) {
        fileIcon.textContent = 'PDF';
        fileIcon.style.backgroundColor = '#FF4444';
    } else if (file.type.includes('word')) {
        fileIcon.textContent = 'DOC';
        fileIcon.style.backgroundColor = '#2196F3';
    }
    
    document.getElementById('resumeFileInfo').style.display = 'flex';
}

function clearResumeFile() {
    resumeFile = null;
    resumeFileInput.value = '';
    document.getElementById('resumeFileInfo').style.display = 'none';
}

// Form submission
const uploadForm = document.getElementById('uploadForm');
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Check if resume file is uploaded
    if (!resumeFile) {
        showAlert('Please upload your resume', 'error');
        return;
    }
    
    // Check credits
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    if (!userData.credits || userData.credits < 1) {
        showAlert('Insufficient credits! Please purchase more credits.', 'error');
        setTimeout(() => {
            window.location.href = 'payment.html';
        }, 2000);
        return;
    }
    
    // Get job description text
    const jobDescText = document.getElementById('jobDescText').value.trim();
    
    // Show loading
    toggleLoading(true);
    
    try {
        // Validate authentication before making request
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            throw new Error('Authentication token not found. Please log in again.');
        }
        
        console.log('🔐 Using auth token:', authToken.substring(0, 20) + '...');
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('resumeFile', resumeFile);
        formData.append('jobDescription', jobDescText);
        
        console.log('📤 Sending request to /api/resume/process...');
        
        // Call backend API for text extraction
        const response = await fetch('/api/resume/process', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        console.log('📥 Response status:', response.status);
        
        const result = await response.json();
        console.log('📥 Response data:', result);
        
        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 401) {
                console.log('❌ 401 Unauthorized - clearing auth and redirecting');
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userData');
                showAlert('Session expired. Please log in again.', 'error');
                setTimeout(() => window.location.href = 'index.html', 2000);
                return;
            }
            throw new Error(result.error || `Server error: ${response.status}`);
        }
        
        console.log('✅ Resume processing successful:', result);
        
        // Simulate successful resume generation for now
        const newResume = {
            id: Date.now(),
            date: new Date().toLocaleDateString(),
            originalFile: resumeFile.name,
            jobDesc: jobDescText ? 'Text provided' : 'None',
            status: 'Completed',
            downloadUrl: '#' // This would be the actual download URL from backend
        };
        
        // Update user data
        userData.credits -= 1;
        userData.resumesGenerated = (userData.resumesGenerated || 0) + 1;
        userData.creditsUsed = (userData.creditsUsed || 0) + 1;
        
        // Save resume to history
        const resumeHistory = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
        resumeHistory.unshift(newResume);
        localStorage.setItem('resumeHistory', JSON.stringify(resumeHistory));
        
        localStorage.setItem('userData', JSON.stringify(userData));
        
        toggleLoading(false);
        
        // Show success modal
        const modal = document.getElementById('successModal');
        modal.classList.add('show');
        
        // Reset form
        clearResumeFile();
        document.getElementById('jobDescText').value = '';
        
        // Update stats
        loadUserData();
        
    } catch (error) {
        console.error('❌ Resume processing failed:', error);
        toggleLoading(false);
        showAlert(error.message || 'Failed to process resume. Please try again.', 'error');
    }
});

// Close success modal
function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.remove('show');
}

// Load resume history
function loadResumeHistory() {
    try {
        const resumeHistory = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
        const tableBody = document.getElementById('recentResumesTable');
        
        if (!tableBody) {
            console.error('Resume table not found');
            return;
        }
        
        if (resumeHistory.length === 0) {
            tableBody.innerHTML = `
                <div class="table-row" style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #666;">
                    No resumes generated yet. Upload your first resume to get started!
                </div>
            `;
            return;
        }
        
        // Show only recent 5 resumes
        const recentResumes = resumeHistory.slice(0, 5);
        tableBody.innerHTML = recentResumes.map(resume => `
            <div class="table-row">
                <div class="table-cell">${resume.date}</div>
                <div class="table-cell">${resume.originalFile}</div>
                <div class="table-cell"><span class="badge badge-success">${resume.status}</span></div>
                <div class="table-cell">
                    <button class="btn-primary" onclick="downloadResume('${resume.id}')">
                        📥 Download
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading resume history:', error);
    }
}

// Download resume
function downloadResume(id) {
    showAlert('Download started! (Demo mode)', 'success');
    // In real implementation, fetch and download the actual PDF
}

// Logout handler
document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('isLoggedIn');
    window.location.href = 'index.html';
});

// Initialize on page load
loadUserData();
