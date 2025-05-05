// static/js/login_register.js
document.addEventListener('DOMContentLoaded', function () {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    const titleElement = document.querySelector('.title');
    const loginRoleInput = document.getElementById('login-role');
    const registerRoleInput = document.getElementById('register-role');
    const loginErrorDiv = document.getElementById('login-error');
    const registerErrorDiv = document.getElementById('register-error');

    // --- Determine Role and Set Title ---
    const role = loginRoleInput.value; // Get role from hidden input rendered by Flask
    if (role === 'doctor') {
        titleElement.textContent = 'Doctor Portal';
    } else {
        titleElement.textContent = 'Patient Portal';
    }

    // --- Tab Switching Logic ---
    loginTab.addEventListener('click', () => {
        setActiveTab(loginTab);
        showForm(loginForm);
    });

    registerTab.addEventListener('click', () => {
        setActiveTab(registerTab);
        showForm(registerForm);
    });

    function setActiveTab(activeTab) {
        loginTab.classList.remove('active');
        registerTab.classList.remove('active');
        activeTab.classList.add('active');
    }

    function showForm(activeForm) {
        loginForm.classList.remove('active');
        registerForm.classList.remove('active');
        activeForm.classList.add('active');
        // Clear any previous error messages when switching forms
        hideError(loginErrorDiv);
        hideError(registerErrorDiv);
    }

    // --- Form Submission Logic ---

    // LOGIN
    signinForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError(loginErrorDiv); // Clear previous errors
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
                // Role is determined server-side based on user data
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Redirect based on the role received from the server
                if (result.role === 'doctor') {
                    window.location.href = '/doctor/dashboard';
                } else {
                    window.location.href = '/home'; // Patient home
                }
            } else {
                showError(loginErrorDiv, result.error || 'Login failed. Please check your credentials.');
            }
        } catch (error) {
            console.error('Login error:', error);
            showError(loginErrorDiv, 'An error occurred during login. Please try again.');
        }
    });

    // REGISTER
    signupForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError(registerErrorDiv); // Clear previous errors

        const name = document.getElementById('register-name').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        const role = registerRoleInput.value; // Get role from hidden input

        if (password !== confirmPassword) {
            showError(registerErrorDiv, 'Passwords do not match.');
            return;
        }
        if (password.length < 6) {
             showError(registerErrorDiv, 'Password must be at least 6 characters long.');
             return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password, role })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Registration successful - show login form with a success message (optional)
                alert('Registration successful! Please sign in.'); // Simple alert
                setActiveTab(loginTab); // Switch to login tab
                showForm(loginForm);
                document.getElementById('login-email').value = email; // Pre-fill email
                document.getElementById('login-password').value = ''; // Clear password
                document.getElementById('login-email').focus();
            } else {
                 showError(registerErrorDiv, result.error || 'Registration failed.');
            }
        } catch (error) {
            console.error('Registration error:', error);
            showError(registerErrorDiv, 'An error occurred during registration. Please try again.');
        }
    });

    // --- Error Display Helpers ---
    function showError(divElement, message) {
        divElement.textContent = message;
        divElement.style.display = 'block';
    }

    function hideError(divElement) {
        divElement.textContent = '';
        divElement.style.display = 'none';
    }

    // --- Initial Setup ---
    // Ensure the correct form is shown based on which tab might be active initially (if needed)
    if (loginTab.classList.contains('active')) {
        showForm(loginForm);
    } else {
        showForm(registerForm);
    }
});