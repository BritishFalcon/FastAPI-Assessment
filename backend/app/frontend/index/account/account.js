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

                // This was a pain, but adding the trigger immediately within the account area change works
                const accountTrigger = document.getElementById('account-popup-trigger');
                const accountPopup = document.getElementById('account-popup');
                const closeAccountPopup = document.getElementById('close-account-popup');

                accountTrigger.addEventListener("click", function (e) {
                    e.preventDefault();
                    accountPopup.style.display = 'block';
                });

                closeAccountPopup.addEventListener("click", function () {
                    accountPopup.style.display = 'none';
                });

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

const signupButton = document.getElementById('signup-button');

if (signupButton) {
    signupButton.addEventListener("click", async function () {
        var email = document.getElementById('signup-email').value;
        var password = document.getElementById('signup-password').value;

        var signupURL = `/signup?email=${email}&password=${password}`;
        const response = await fetch(signupURL, { method: 'POST' });

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

const loginButton = document.getElementById('leaflet-button');

if (loginButton) {
    loginButton.addEventListener("click", async function () {
        var email = document.getElementById('leaflet-email').value;
        var password = document.getElementById('leaflet-password').value;

        var loginURL = `/login?email=${email}&password=${password}`;
        const response = await fetch(loginURL, { method: 'POST' });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            document.getElementById('leaflet-popup').style.display = 'none';

            // As before, easier to reload the page
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
        localStorage.removeItem('access_token');
        location.reload();
    });
}