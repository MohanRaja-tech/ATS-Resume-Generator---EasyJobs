// Profile JavaScript
// Handles profile management, resume history, and transaction history

// Utility function to safely update element text content
function safeUpdateElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    } else {
        console.warn(`Element with ID '${elementId}' not found`);
    }
}

// Initialize user data on page load
function initializeUserData() {
    // Set demo data if not exists (for migration from old system)
    if (!localStorage.getItem('userData')) {
        const demoUserData = {
            email: 'demo@easyjobs.com',
            name: 'Demo User',
            credits: 5,
            resumesGenerated: 0,
            creditsUsed: 0,
            creditsPurchased: 5,
            credits_purchased: 5,
            credits_used: 0,
            resumes_generated: 0,
            memberSince: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
            member_since: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
        };
        localStorage.setItem('userData', JSON.stringify(demoUserData));
    }

    // Set auth flags if not exists
    if (!localStorage.getItem('isLoggedIn')) {
        localStorage.setItem('isLoggedIn', 'true');
    }
    if (!localStorage.getItem('authToken')) {
        // Create a simple demo token (base64 encoded JSON)
        const demoToken = btoa(JSON.stringify({
            user_id: 'demo_user_' + Date.now(),
            email: 'demo@easyjobs.com',
            exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
        }));
        const fullDemoToken = 'header.' + demoToken + '.signature';
        localStorage.setItem('authToken', fullDemoToken);
    }
}

// Initialize profile page
initializeUserData();

// Utility functions
function showAlert(message, type = 'success') {
    // Remove any existing alerts
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} show`;
    alert.textContent = message;

    // Insert after the header
    const header = document.querySelector('header');
    header.insertAdjacentElement('afterend', alert);

    setTimeout(() => {
        alert.remove();
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

// Load user data from MongoDB via API
async function loadUserData() {
    toggleLoading(true);

    try {
        const authToken = localStorage.getItem('authToken');
        const response = await fetch('/api/user/profile', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            // Don't redirect, just fall back to localStorage
            throw new Error('Failed to fetch user data from API');
        }

        const data = await response.json();

        // Update profile information
        const fullName = data.name || 'User';
        safeUpdateElement('userNameDisplay', fullName);

        // Update the new container-based display elements
        safeUpdateElement('nameDisplay', fullName);
        safeUpdateElement('emailDisplay', data.email || '');

        // Format member since date
        const memberSince = new Date(data.created_at).toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        });
        if (document.getElementById('memberSinceDisplay')) {
            document.getElementById('memberSinceDisplay').textContent = memberSince;
        }

        // Update initials - check if element exists first
        const initials = (data.name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        safeUpdateElement('userInitials', initials);

        // Update credits information
        safeUpdateElement('totalCredits', data.credits || 0);
        safeUpdateElement('totalCreditsCard', data.credits || 0);
        safeUpdateElement('creditsPurchased', data.credits_purchased || 0);
        safeUpdateElement('creditsUsed', data.credits_used || 0);
        safeUpdateElement('resumesCount', data.resumes_generated || 0);

        // Load histories
        loadResumeHistory();
        loadTransactionHistory();

    } catch (error) {
        console.error('Error loading user data:', error);

        // Fallback to localStorage data if API fails
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');

        if (userData && userData.email) {
            // Update profile information from localStorage
            const fullName = userData.name || 'Demo User';
            safeUpdateElement('userNameDisplay', fullName);

            // Update the new container-based display elements
            safeUpdateElement('nameDisplay', fullName);
            safeUpdateElement('emailDisplay', userData.email || '');
            safeUpdateElement('memberSinceDisplay', userData.member_since || userData.memberSince || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }));

            // Update initials
            const initials = (userData.name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            safeUpdateElement('userInitials', initials);

            // Update credits information
            safeUpdateElement('totalCredits', userData.credits || 0);
            safeUpdateElement('totalCreditsCard', userData.credits || 0);
            safeUpdateElement('creditsPurchased', userData.credits_purchased || userData.creditsPurchased || 0);
            safeUpdateElement('creditsUsed', userData.credits_used || userData.creditsUsed || 0);
            safeUpdateElement('resumesCount', userData.resumes_generated || userData.resumesGenerated || 0);

            // Load histories
            loadResumeHistory();
            loadTransactionHistory();

            console.log('Using cached user data from localStorage');
        } else {
            showAlert('Failed to load profile data. Please try refreshing the page.', 'error');
        }
    } finally {
        toggleLoading(false);
    }
}

// Load resume history from backend
async function loadResumeHistory() {
    try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            console.log('No auth token available');
            return;
        }

        console.log('📥 Fetching resume history from backend...');

        // Show loading state
        const tableBody = document.getElementById('resumeHistoryTable');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: #6c757d;">
                        <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                            <div style="font-size: 18px; opacity: 0.5;">⏳</div>
                            <span>Loading resume history...</span>
                        </div>
                    </td>
                </tr>
            `;
        }

        // Fetch resumes from backend
        const response = await fetch('/api/resume/user-resumes', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const totalResumes = document.getElementById('totalResumes');

        if (!tableBody) {
            console.error('Resume table element not found');
            return;
        }

        if (!response.ok) {
            if (response.status === 401) {
                console.log('❌ Authentication failed - clearing auth');
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userData');
                // Don't redirect here as user might be viewing profile
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 2rem; color: #f44;">
                            Authentication expired. Please log in again.
                        </td>
                    </tr>
                `;
                return;
            }
            throw new Error(`Failed to fetch resumes: ${response.status}`);
        }

        const result = await response.json();
        console.log('📥 Resume history response:', result);

        if (result.success && result.data && result.data.resumes && result.data.resumes.length > 0) {
            const resumes = result.data.resumes;
            safeUpdateElement('totalResumes', resumes.length);

            tableBody.innerHTML = resumes.map(resume => {
                const date = new Date(resume.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
                const filename = resume.originalFile || resume.original_filename || 'Resume.pdf';
                const fileSize = resume.file_size_kb ? `${resume.file_size_kb} KB` : '';
                const downloadCount = resume.download_count || 0;


                // Debug: Check what ID field exists
                const resumeId = resume._id || resume.id || resume.resume_id;
                console.log('Resume object:', resume);
                console.log('Resume ID found:', resumeId);
                console.log('Filename fields:', {
                    original_filename: resume.original_filename,
                    filename: resume.filename,
                    file_name: resume.file_name,
                    originalFilename: resume.originalFilename
                });

                return `
                    <tr>
                        <td style="font-weight: 600; white-space: nowrap;">${date}</td>
                        <td style="word-wrap: break-word; white-space: normal;">
                            <div style="font-weight: 600; margin-bottom: 2px; word-break: break-word;">${filename}</div>
                            ${fileSize ? `<div style="font-size: 12px; color: #666;">${fileSize}</div>` : ''}
                        </td>
                        <td><span class="badge badge-success">Completed</span></td>
                        <td style="text-align: center; font-weight: 600;">${downloadCount}</td>
                        <td>
                            <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="downloadResumeFromBackend('${resumeId}')" title="Download ${filename}">
                                <i class="fas fa-download"></i> Download
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            console.log(`✅ Loaded ${resumes.length} resumes in profile`);
        } else {
            safeUpdateElement('totalResumes', '0');
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
                        No resume history yet. Generate your first resume to see it here!
                    </td>
                </tr>
            `;
        }

    } catch (error) {
        console.error('❌ Error loading resume history:', error);

        const tableBody = document.getElementById('resumeHistoryTable');

        safeUpdateElement('totalResumes', '0');
        if (tableBody) {
            // Try localStorage fallback
            try {
                const localResumes = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
                if (localResumes.length > 0) {
                    console.log('📦 Using localStorage fallback in profile');
                    tableBody.innerHTML = localResumes.map(resume => `
                        <tr>
                            <td style="font-weight: 600;">${resume.date}</td>
                            <td>
                                <div style="font-weight: 600;">${resume.originalFile}</div>
                            </td>
                            <td><span class="badge badge-success">${resume.status}</span></td>
                            <td style="text-align: center; font-weight: 600;">0</td>
                            <td>
                                <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="downloadResume('${resume.id}')" title="Download ${resume.originalFile}"
                                        ${!resume.downloadUrl || resume.downloadUrl === '#' ? 'disabled' : ''}>
                                    <i class="fas fa-download"></i> Download
                                </button>
                            </td>
                        </tr>
                    `).join('');
                    safeUpdateElement('totalResumes', localResumes.length);
                } else {
                    throw new Error('No local data');
                }
            } catch (localError) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 2rem; color: #f44;">
                            Failed to load resume history. Please refresh the page.
                        </td>
                    </tr>
                `;
            }
        }
    }
}

// Download resume from backend by ID
async function downloadResumeFromBackend(resumeId) {
    try {
        console.log(`📥 Downloading resume: ${resumeId}`);

        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            showAlert('Please log in to download resumes', 'error');
            return;
        }

        // Show loading indicator
        showAlert('Preparing download...', 'info');

        // Fetch resume from backend
        const response = await fetch(`/api/resume/download/${resumeId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                showAlert('Session expired. Please log in again.', 'error');
                setTimeout(() => window.location.href = 'index.html', 2000);
                return;
            }
            throw new Error(`Failed to download resume: ${response.status}`);
        }

        // Get the blob from response
        const blob = await response.blob();

        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'resume.pdf';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }

        // Create download link
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up
        URL.revokeObjectURL(downloadUrl);

        showAlert('Download started!', 'success');
        console.log('✅ Resume downloaded successfully');

    } catch (error) {
        // Legacy localStorage download
        try {
            const resumeHistory = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
            const resume = resumeHistory.find(r => r.id == resumeId);

            if (!resume) {
                showAlert('Resume not found', 'error');
                return;
            }

            if (!resume.downloadUrl || resume.downloadUrl === '#') {
                showAlert('Download not available for this resume', 'error');
                return;
            }

            // Create download link
            const link = document.createElement('a');
            link.href = resume.downloadUrl;
            link.download = resume.filename || `resume_${resume.id}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            showAlert('Download started!', 'success');

        } catch (error) {
            console.error('Download error:', error);
            showAlert('Failed to download resume', 'error');
        }
    }
}

// Load transaction history
function loadTransactionHistory() {
    const transactions = JSON.parse(localStorage.getItem('transactions') || '[]');
    const tableBody = document.getElementById('transactionHistoryTable');

    // Add welcome bonus if no transactions exist
    if (transactions.length === 0) {
        const welcomeBonus = {
            id: 'TXN-001-INITIAL',
            date: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
            type: 'Welcome Bonus',
            credits: '+5',
            amount: '₹0.00',
            status: 'Completed'
        };
        transactions.push(welcomeBonus);
        localStorage.setItem('transactions', JSON.stringify(transactions));
    }

    tableBody.innerHTML = transactions.map(txn => `
                    < tr >
            <td>${txn.date}</td>
            <td>${txn.id}</td>
            <td>${txn.type}</td>
            <td style="color: ${txn.credits.includes('+') ? '#28A745' : '#DC3545'}; font-weight: 600;">${txn.credits}</td>
            <td>${txn.amount}</td>
            <td><span class="badge badge-success">${txn.status}</span></td>
        </tr >
                    `).join('');
}

// Initialize on page load
loadUserData();
