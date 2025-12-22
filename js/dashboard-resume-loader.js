// Load resume history from backend
async function loadResumeHistory() {
    try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            console.log('No auth token available');
            return;
        }

        console.log('📥 Fetching resume history from backend...');

        // Fetch resumes from backend
        const response = await fetch('/api/resume/user-resumes?limit=5', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const tableBody = document.getElementById('recentResumesTable');

        if (!tableBody) {
            console.error('Resume table not found');
            return;
        }

        if (!response.ok) {
            if (response.status === 401) {
                console.log('❌ Authentication failed - clearing auth');
                localStorage.removeItem('authToken');
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userData');
                return;
            }
            throw new Error(`Failed to fetch resumes: ${response.status}`);
        }

        const result = await response.json();
        console.log('📥 Resume history response:', result);

        if (result.success && result.data && result.data.resumes && result.data.resumes.length > 0) {
            const resumes = result.data.resumes;

            tableBody.innerHTML = resumes.map(resume => `
                <tr>
                    <td class="table-cell">${resume.date}</td>
                    <td class="table-cell">
                        ${resume.originalFile}
                        ${resume.file_size_kb ? `<br><small style="color: #666;">${resume.file_size_kb} KB</small>` : ''}
                    </td>
                    <td class="table-cell"><span class="badge badge-success">${resume.status}</span></td>
                    <td class="table-cell">
                        <button class="btn btn-primary" onclick="downloadResumeFromBackend('${resume.id}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </td>
                </tr>
            `).join('');

            console.log(`✅ Loaded ${resumes.length} resumes`);
        } else {
            console.log('📥 No resumes found or empty response');
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 2rem; color: #666;">
                        No resumes generated yet. Upload your first resume to get started!
                    </td>
                </tr>
            `;
        }

    } catch (error) {
        console.error('❌ Error loading resume history:', error);
        console.error('Error details:', error.message, error.stack);

        const tableBody = document.getElementById('recentResumesTable');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; padding: 2rem; color: #f44;">
                        Failed to load resume history: ${error.message}. Please refresh the page.
                    </td>
                </tr>
            `;
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
            // Match filename with or without quotes, non-greedy capture
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1].trim();
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
        console.error('❌ Error downloading resume:', error);
        showAlert(error.message || 'Failed to download resume. Please try again.', 'error');
    }
}

// Call loadResumeHistory when page loads
window.addEventListener('load', function () {
    console.log('Dashboard resume loader initialized');
    // Wait a bit for other scripts to finish
    setTimeout(loadResumeHistory, 500);
});
