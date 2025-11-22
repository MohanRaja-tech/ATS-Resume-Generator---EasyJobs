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

        // Set auth flags if not exists  
        if (!localStorage.getItem('authToken')) {
            // Create a simple demo token (matches backend demo support)
            const demoToken = btoa(JSON.stringify({
                user_id: 'demo_user_12345',
                email: 'demo@easyjobs.com'
            }));
            localStorage.setItem('authToken', demoToken);
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

// Store generated resume data for download
let generatedResumeData = null;

// Helper function to download PDF from base64 data
function downloadPdfFromBase64(base64Data, filename) {
    try {
        // Convert base64 to blob
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log('✅ PDF downloaded successfully');
    } catch (error) {
        console.error('❌ Download error:', error);
        showAlert('Failed to download PDF. Please try again.', 'error');
    }
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

        console.log('📤 Step 1: Sending request to /api/resume/process for text extraction...');

        // Step 1: Call backend API for text extraction
        const processResponse = await fetch('/api/resume/process', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });

        console.log('📥 Text extraction response status:', processResponse.status);

        const processResult = await processResponse.json();
        console.log('📥 Text extraction response data:', processResult);

        if (!processResponse.ok) {
            // Handle specific error cases
            if (processResponse.status === 401) {
                console.log('❌ 401 Unauthorized - clearing auth and redirecting');
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userData');
                showAlert('Session expired. Please log in again.', 'error');
                setTimeout(() => window.location.href = 'index.html', 2000);
                return;
            }
            throw new Error(processResult.error || `Server error: ${processResponse.status}`);
        }

        console.log('✅ Text extraction successful');

        // Step 2: Call AWS API to generate optimized resume
        console.log('📤 Step 2: Sending request to /api/resume/generate-resume for AWS processing...');

        const generateResponse = await fetch('/api/resume/generate-resume', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                job_description: jobDescText
            })
        });

        console.log('📥 Resume generation response status:', generateResponse.status);

        const generateResult = await generateResponse.json();
        console.log('📥 Resume generation response data:', generateResult);

        if (!generateResponse.ok) {
            if (generateResponse.status === 401) {
                console.log('❌ 401 Unauthorized - clearing auth and redirecting');
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userData');
                showAlert('Session expired. Please log in again.', 'error');
                setTimeout(() => window.location.href = 'index.html', 2000);
                return;
            }
            throw new Error(generateResult.error || `Resume generation failed: ${generateResponse.status}`);
        }

        console.log('✅ Resume generation successful');

        // Store generated resume data for manual download
        generatedResumeData = {
            resume_id: generateResult.data.resume_id,
            pdf_base64: generateResult.data.pdf_base64,
            filename: generateResult.data.original_filename || resumeFile.name
        };

        // Step 3: Auto-download the generated PDF
        console.log('📥 Step 3: Auto-downloading generated PDF...');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const downloadFilename = `optimized_resume_${timestamp}.pdf`;
        downloadPdfFromBase64(generateResult.data.pdf_base64, downloadFilename);

        // Update user data
        userData.credits -= 1;
        userData.resumesGenerated = (userData.resumesGenerated || 0) + 1;
        userData.creditsUsed = (userData.creditsUsed || 0) + 1;
        localStorage.setItem('userData', JSON.stringify(userData));

        toggleLoading(false);

        // Show success modal
        const modal = document.getElementById('successModal');
        modal.classList.add('show');

        // Reset form
        clearResumeFile();
        document.getElementById('jobDescText').value = '';

        // Update stats and reload resume history
        loadUserData();

    } catch (error) {
        console.error('❌ Resume generation failed:', error);
        toggleLoading(false);
        showAlert(error.message || 'Failed to generate resume. Please try again.', 'error');
    }
});

// Close success modal
function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.remove('show');
}

// Manual download from success modal
function downloadFromModal() {
    if (generatedResumeData && generatedResumeData.pdf_base64) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `optimized_resume_${timestamp}.pdf`;
        downloadPdfFromBase64(generatedResumeData.pdf_base64, filename);
        showAlert('Download started!', 'success');
    } else {
        showAlert('No resume data available. Please generate a new resume.', 'error');
    }
}


// Load resume history from backend
async function loadResumeHistory() {
    try {
        const tableBody = document.getElementById('recentResumesTable');

        if (!tableBody) {
            console.error('❌ Resume table not found');
            return;
        }

        console.log('📥 Fetching resume history from backend...');
        console.log('📥 Fetching resume history from backend...');

        // Get auth token
        const authToken = localStorage.getItem('authToken');
        console.log('🔑 Auth token:', authToken ? 'Present' : 'Missing');
        if (!authToken) {
            console.error('❌ No auth token found');
            return;
        }

        console.log('🌐 Making API request to /api/resume/user-resumes...');

        // Fetch resumes from backend
        const response = await fetch('/api/resume/user-resumes?limit=5', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('📡 API response status:', response.status);

        if (!response.ok) {
            if (response.status === 401) {
                console.error('❌ Authentication failed');
                // Clear invalid auth and redirect
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                window.location.href = 'index.html';
                return;
            }
            throw new Error(`Failed to fetch resumes: ${response.status}`);
        }

        const data = await response.json();
        const resumes = data.data?.resumes || [];

        console.log(`✅ Loaded ${resumes.length} resumes from backend`);

        if (resumes.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 3rem 2rem; color: #6c757d;">
                        <div style="display: flex; flex-direction: column; align-items: center; gap: 16px;">
                            <div style="font-size: 48px; opacity: 0.3;">📄</div>
                            <div style="font-size: 18px; font-weight: 600; color: #495057;">No resumes generated yet</div>
                            <div style="font-size: 14px; color: #6c757d;">Upload your first resume to get started!</div>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // Display resumes in table
        tableBody.innerHTML = resumes.map(resume => {
            const date = new Date(resume.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
            const fileSize = resume.file_size_kb ? `${resume.file_size_kb} KB` : '';
            const filename = resume.original_filename || 'Resume.pdf';

            return `
                <tr>
                    <td style="font-weight: 600; color: #6c757d;">${date}</td>
                    <td>
                        <div class="filename-primary">${filename}</div>
                        ${fileSize ? `<div class="filename-secondary">${fileSize}</div>` : ''}
                    </td>
                    <td><span class="badge badge-success">Completed</span></td>
                    <td>
                        <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="downloadResumeFromBackend('${resume._id}')" title="Download ${filename}">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('❌ Error loading resume history:', error);

        // Fallback to localStorage if backend fails
        try {
            console.log('🔄 Falling back to localStorage...');
            const resumeHistory = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
            const tableBody = document.getElementById('recentResumesTable');

            if (resumeHistory.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" style="text-align: center; padding: 3rem 2rem; color: #6c757d;">
                            <div style="display: flex; flex-direction: column; align-items: center; gap: 16px;">
                                <div style="font-size: 48px; opacity: 0.3;">📄</div>
                                <div style="font-size: 18px; font-weight: 600; color: #495057;">No resumes found</div>
                                <div style="font-size: 14px; color: #6c757d;">Upload your first resume to get started!</div>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            // Show only recent 5 resumes from localStorage
            const recentResumes = resumeHistory.slice(0, 5);
            tableBody.innerHTML = recentResumes.map(resume => `
                <tr>
                    <td style="font-weight: 600; color: #6c757d;">${resume.date}</td>
                    <td>
                        <div class="filename-primary">${resume.originalFile}</div>
                    </td>
                    <td><span class="badge badge-success">${resume.status}</span></td>
                    <td>
                        <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="downloadResume('${resume.id}')" title="Download ${resume.originalFile}">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </td>
                </tr>
            `).join('');

            console.log('✅ Loaded resume history from localStorage fallback');
        } catch (fallbackError) {
            console.error('❌ Fallback error:', fallbackError);
        }
    }
}

// Download resume from backend by ID
async function downloadResumeFromBackend(resumeId) {
    try {
        showAlert('Preparing download...', 'info');

        // Get auth token
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            showAlert('Authentication required', 'error');
            return;
        }

        console.log(`📥 Downloading resume: ${resumeId}`);

        // Fetch resume from backend
        const response = await fetch(`/api/resume/download/${resumeId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                showAlert('Resume not found', 'error');
                return;
            }
            if (response.status === 401) {
                showAlert('Authentication failed', 'error');
                return;
            }
            throw new Error(`Download failed: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.pdf_data) {
            // Convert base64 to blob
            const byteCharacters = atob(data.pdf_data);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/pdf' });

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename || `resume_${resumeId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showAlert('Download completed successfully!', 'success');
            console.log('✅ Resume downloaded successfully');
        } else {
            showAlert('Failed to download resume', 'error');
        }

    } catch (error) {
        console.error('❌ Download error:', error);
        showAlert('Download failed. Please try again.', 'error');
    }
}

// Legacy download function for localStorage fallback
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
