document.addEventListener("DOMContentLoaded", function () {
    // Check storage for a token
    const token = localStorage.getItem('access_token');

    if (token) {
        var verify_url = '/validate?token=' + token;
        fetch(verify_url, { method: 'GET' }
        ).then(async function (response) {
            if (response.ok) {
                const data = await response.json();
                return {
                    loggedIn: true,
                    username: data.email
                };
            } else {
                localStorage.removeItem('access_token');
                return { loggedIn: false };
            }
        }).then(function (user) {
            const accountArea = document.getElementById("account-area");

            if (user.loggedIn) {
                accountArea.innerHTML = `
                    <span class="username-display">${user.username}</span>
                    <a href="#" id="account-popup-trigger" class="account-button">Account</a>
                `;
            } else {
                accountArea.innerHTML = `
                    <a href="#" id="login-trigger" class="account-link">Log In</a>
                    <span class="separator">|</span>
                    <a href="#" id="signup-trigger" class="account-link">Sign Up</a>
                `;
            }
        }
        );
    } else {
        const accountArea = document.getElementById("account-area");
        accountArea.innerHTML = `
            <a href="#" id="login-trigger" class="account-link">Log In</a>
            <span class="separator">|</span>
            <a href="#" id="signup-trigger" class="account-link">Sign Up</a>
        `;
    }
});

const accountTrigger = document.getElementById('account-popup-trigger');
const accountPopup = document.getElementById('account-popup');
const closeAccountPopup = document.getElementById('close-account-popup');

if (accountTrigger) {
    accountTrigger.addEventListener("click", function (e) {
        e.preventDefault();
        accountPopup.style.display = 'block';
    });
}

if (closeAccountPopup) {
    closeAccountPopup.addEventListener("click", function () {
        accountPopup.style.display = 'none';
    });
}

const signupButton = document.getElementById('signup-button');

if (signupButton) {
    signupButton.addEventListener("click", async function () {
        var email = document.getElementById('signup-email').value;
        var password = document.getElementById('signup-password').value;

        var signupURL = `/signup?email=${email}&password=${password}`;
        const response = await fetch(signupURL, { method: 'POST' });

        // Validate this is correct methodology for JWT-auth
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            document.getElementById('signup-popup').style.display = 'none';

            // Reload page for ease of re-initialisation on sign-up
            location.reload();
        } else {
            const error = await response.text();
            alert(error);
        }


    });
}

const logoutButton = document.getElementById('logout-button');

if (logoutButton) {
    logoutButton.addEventListener("click", function () {
        // TODO: Implement logout functionality
    });
}