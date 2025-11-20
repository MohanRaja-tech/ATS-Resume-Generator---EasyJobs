// Profile JavaScript
// Handles profile management, resume history, and transaction history

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
        localStorage.setItem('authToken', 'demo_token_' + Date.now());
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
        document.getElementById('userNameDisplay').textContent = fullName;
        
        // Update the new container-based display elements
        if (document.getElementById('nameDisplay')) {
            document.getElementById('nameDisplay').textContent = fullName;
        }
        if (document.getElementById('emailDisplay')) {
            document.getElementById('emailDisplay').textContent = data.email || '';
        }
        
        // Format member since date
        const memberSince = new Date(data.created_at).toLocaleDateString('en-US', { 
            month: 'long', 
            day: 'numeric', 
            year: 'numeric' 
        });
        if (document.getElementById('memberSinceDisplay')) {
            document.getElementById('memberSinceDisplay').textContent = memberSince;
        }
        
        // Update initials
        const initials = (data.name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        document.getElementById('userInitials').textContent = initials;
        
        // Update credits information
        document.getElementById('totalCredits').textContent = data.credits || 0;
        document.getElementById('totalCreditsCard').textContent = data.credits || 0;
        document.getElementById('creditsPurchased').textContent = data.credits_purchased || 0;
        document.getElementById('creditsUsed').textContent = data.credits_used || 0;
        document.getElementById('resumesCount').textContent = data.resumes_generated || 0;
        
        // Load histories
        loadResumeHistory();
        loadTransactionHistory();
        
    } catch (error) {
        console.error('Error loading user data:', error);
        
        // Fallback to localStorage data if API fails
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        
        if (userData && userData.email) {
            // Update profile information from localStorage
            const fullName = userData.name || 'User';
            document.getElementById('userNameDisplay').textContent = fullName;
            
            // Update the new container-based display elements
            if (document.getElementById('nameDisplay')) {
                document.getElementById('nameDisplay').textContent = fullName;
            }
            if (document.getElementById('emailDisplay')) {
                document.getElementById('emailDisplay').textContent = userData.email || '';
            }
            if (document.getElementById('memberSinceDisplay')) {
                document.getElementById('memberSinceDisplay').textContent = userData.member_since || userData.memberSince || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
            }
            
            // Update initials
            const initials = (userData.name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            document.getElementById('userInitials').textContent = initials;
            
            // Update credits information
            document.getElementById('totalCredits').textContent = userData.credits || 0;
            document.getElementById('totalCreditsCard').textContent = userData.credits || 0;
            document.getElementById('creditsPurchased').textContent = userData.credits_purchased || userData.creditsPurchased || 0;
            document.getElementById('creditsUsed').textContent = userData.credits_used || userData.creditsUsed || 0;
            document.getElementById('resumesCount').textContent = userData.resumes_generated || userData.resumesGenerated || 0;
            
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

// Load resume history
function loadResumeHistory() {
    const resumeHistory = JSON.parse(localStorage.getItem('resumeHistory') || '[]');
    const tableBody = document.getElementById('resumeHistoryTable');
    const totalResumes = document.getElementById('totalResumes');
    
    totalResumes.textContent = resumeHistory.length;
    
    if (resumeHistory.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 2rem; color: #666;">
                    No resume history yet. Generate your first resume to see it here!
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = resumeHistory.map(resume => `
        <tr>
            <td>${resume.date}</td>
            <td>${resume.originalFile}</td>
            <td><span class="badge badge-success">${resume.status}</span></td>
            <td>
                <button class="btn btn-primary" style="padding: 0.5rem 1rem;" onclick="downloadResume('${resume.id}')">
                    <i class="fas fa-download"></i> Download
                </button>
            </td>
        </tr>
    `).join('');
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
        <tr>
            <td>${txn.date}</td>
            <td>${txn.id}</td>
            <td>${txn.type}</td>
            <td style="color: ${txn.credits.includes('+') ? '#28A745' : '#DC3545'}; font-weight: 600;">${txn.credits}</td>
            <td>${txn.amount}</td>
            <td><span class="badge badge-success">${txn.status}</span></td>
        </tr>
    `).join('');
}

// Download resume
function downloadResume(id) {
    showAlert('Download started! (Demo mode)', 'success');
    // In real implementation, fetch and download the actual PDF
}

// Initialize on page load
loadUserData();
