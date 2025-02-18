document.addEventListener("DOMContentLoaded", function () {
    const loginTrigger = document.getElementById('login-trigger');
    const signupTrigger = document.getElementById('signup-trigger');
    const accountTrigger = document.getElementById('account-popup-trigger');

    const loginPopup = document.getElementById('login-popup');
    const signupPopup = document.getElementById('signup-popup');
    const accountPopup = document.getElementById('account-popup');

    const closeLoginPopup = document.getElementById('close-login-popup');
    const closeSignupPopup = document.getElementById('close-signup-popup');
    const closeAccountPopup = document.getElementById('close-account-popup');


    if (loginTrigger) {
        loginTrigger.addEventListener("click", function (e) {
            e.preventDefault();
            loginPopup.style.display = 'block';
        });
    }

    if (signupTrigger) {
        signupTrigger.addEventListener("click", function (e) {
            e.preventDefault();
            signupPopup.style.display = 'block';
        });
    }

    if (closeLoginPopup) {
        closeLoginPopup.addEventListener("click", function () {
            loginPopup.style.display = 'none';
        });
    }

    if (closeSignupPopup) {
        closeSignupPopup.addEventListener("click", function () {
            signupPopup.style.display = 'none';
        });
    }
});