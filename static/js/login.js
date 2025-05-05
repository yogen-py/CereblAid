document.addEventListener('DOMContentLoaded', function () {
    // Check authentication
    checkAuthentication();

    const signinForm = document.getElementById('signin-form');
    signinForm.addEventListener('submit', function (e) {
        e.preventDefault();
        login();
    });

    async function login() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const role = document.querySelector('.role-btn.active').id.split('-')[0]; // Get role from active button

        const data = {
            email: email,
            password: password,
            role: role
        };

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });

            const result = await response.json();
            if (result.success) {
                window.location.href = '/'; // Redirect to the dashboard
            } else {
                alert(result.error); // Show error message
            }
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed, please try again.');
        }
    }

    async function checkAuthentication() {
        try {
            const response = await fetch('/api/check-auth', {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (!data.authenticated) {
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            window.location.href = '/login';
        }
    }
});
