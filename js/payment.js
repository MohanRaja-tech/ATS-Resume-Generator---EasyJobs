// Payment JavaScript
// Handles credit purchase and Razorpay integration

// Check authentication
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const authToken = localStorage.getItem('authToken');
    
    if (!isLoggedIn || isLoggedIn !== 'true' || !authToken) {
        window.location.href = 'index.html';
        return;
    }
}

// Initialize payment page
checkAuth();

// Load user data
function loadUserData() {
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    document.getElementById('currentCredits').textContent = userData.credits || 0;
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

// Selected plan data
let selectedPlanData = null;

// Select plan function
function selectPlan(planName, credits, amount) {
    selectedPlanData = {
        name: planName.charAt(0).toUpperCase() + planName.slice(1),
        credits: credits,
        amount: amount
    };
    
    // Update payment section
    document.getElementById('selectedPlan').textContent = selectedPlanData.name;
    document.getElementById('selectedCredits').textContent = `${selectedPlanData.credits} Credits`;
    document.getElementById('totalAmount').textContent = selectedPlanData.amount;
    document.getElementById('payAmount').textContent = selectedPlanData.amount;
    
    // Show payment section
    document.getElementById('paymentSection').style.display = 'block';
    
    // Scroll to payment section
    document.getElementById('paymentSection').scrollIntoView({ behavior: 'smooth' });
    
    showAlert(`${selectedPlanData.name} plan selected! Complete payment below.`, 'info');
}

// Cancel payment
function cancelPayment() {
    selectedPlanData = null;
    document.getElementById('paymentSection').style.display = 'none';
    document.getElementById('paymentForm').reset();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Format card number
const cardNumberInput = document.getElementById('cardNumber');
if (cardNumberInput) {
    cardNumberInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\s/g, '');
        let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
        e.target.value = formattedValue;
    });
}

// Format expiry date
const expiryDateInput = document.getElementById('expiryDate');
if (expiryDateInput) {
    expiryDateInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = value.slice(0, 2) + '/' + value.slice(2, 4);
        }
        e.target.value = value;
    });
}

// CVV validation
const cvvInput = document.getElementById('cvv');
if (cvvInput) {
    cvvInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 3);
    });
}

// Payment form submission
const paymentForm = document.getElementById('paymentForm');
if (paymentForm) {
    paymentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!selectedPlanData) {
            showAlert('Please select a plan first', 'error');
            return;
        }
        
        // Get form data
        const cardName = document.getElementById('cardName').value.trim();
        const cardNumber = document.getElementById('cardNumber').value.replace(/\s/g, '');
        const expiryDate = document.getElementById('expiryDate').value;
        const cvv = document.getElementById('cvv').value;
        
        // Basic validation
        if (cardNumber.length !== 16) {
            showAlert('Invalid card number', 'error');
            return;
        }
        
        if (cvv.length !== 3) {
            showAlert('Invalid CVV', 'error');
            return;
        }
        
        if (!expiryDate.match(/^\d{2}\/\d{2}$/)) {
            showAlert('Invalid expiry date format', 'error');
            return;
        }
        
        // Show loading
        toggleLoading(true);
        
        // Simulate payment processing (Replace with actual Razorpay integration)
        // In real implementation, you would initialize Razorpay here
        /*
        const options = {
            key: 'YOUR_RAZORPAY_KEY',
            amount: selectedPlanData.amount * 100, // Amount in paise
            currency: 'INR',
            name: 'Resume Generator',
            description: `${selectedPlanData.name} Plan - ${selectedPlanData.credits} Credits`,
            handler: function (response) {
                // Payment successful
                processSuccessfulPayment(response.razorpay_payment_id);
            },
            prefill: {
                name: cardName,
                email: userData.email
            },
            theme: {
                color: '#0000FF'
            }
        };
        const rzp = new Razorpay(options);
        rzp.open();
        */
        
        // Simulate successful payment after 2 seconds
        setTimeout(() => {
            processSuccessfulPayment('DEMO_' + Date.now());
        }, 2000);
    });
}

// Process successful payment
function processSuccessfulPayment(paymentId) {
    // Update user data
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    userData.credits = (userData.credits || 0) + selectedPlanData.credits;
    userData.creditsPurchased = (userData.creditsPurchased || 0) + selectedPlanData.credits;
    localStorage.setItem('userData', JSON.stringify(userData));
    
    // Add transaction to history
    const transactions = JSON.parse(localStorage.getItem('transactions') || '[]');
    const newTransaction = {
        id: paymentId,
        date: new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }),
        type: `${selectedPlanData.name} Plan Purchase`,
        credits: `+${selectedPlanData.credits}`,
        amount: `₹${selectedPlanData.amount}.00`,
        status: 'Completed'
    };
    transactions.unshift(newTransaction);
    localStorage.setItem('transactions', JSON.stringify(transactions));
    
    toggleLoading(false);
    
    // Show success modal
    document.getElementById('creditsAdded').textContent = selectedPlanData.credits;
    const modal = document.getElementById('successModal');
    modal.classList.add('show');
    
    // Update current credits display
    loadUserData();
    
    // Reset form and hide payment section
    paymentForm.reset();
    document.getElementById('paymentSection').style.display = 'none';
    selectedPlanData = null;
}

// Go to dashboard
function goToDashboard() {
    window.location.href = 'dashboard.html';
}

// Logout handler
document.getElementById('logoutBtn').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('isLoggedIn');
    window.location.href = 'index.html';
});

// Initialize on page load
loadUserData();
