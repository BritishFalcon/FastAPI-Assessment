'use client';
import React, { useEffect, useState } from 'react';
import AccountPopup from '../popup/Account';
import LoginPopup from '../popup/Login';
import SignupPopup from '../popup/Signup';
import '../Account.module.css';

export default function AccountArea() {
  const [authChecked, setAuthChecked] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [showAccountPopup, setShowAccountPopup] = useState(false);
  const [showLoginPopup, setShowLoginPopup] = useState(false);
  const [showSignupPopup, setShowSignupPopup] = useState(false);

  // Run auth check only on client mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetch(`/validate?token=${token}`, { method: 'GET' })
        .then(async (response) => {
          if (response.ok) {
            const data = await response.json();
            setLoggedIn(true);
            setUsername(data.email);
          } else {
            localStorage.removeItem('access_token');
            setLoggedIn(false);
          }
          setAuthChecked(true);
        })
        .catch((error) => {
          console.error('Validation error:', error);
          localStorage.removeItem('access_token');
          setLoggedIn(false);
          setAuthChecked(true);
        });
    } else {
      setAuthChecked(true);
    }
  }, []);

  // Until auth is checked, render a static placeholder that matches SSR
  if (!authChecked) {
    return (
      <div className="account">
        <a href="#" className="account-link">Log In</a>
        <span className="separator">|</span>
        <a href="#" className="account-link">Sign Up</a>
      </div>
    );
  }

  return (
    <div className="account">
      {loggedIn ? (
        <>
          <span className="username-display">{username}</span>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setShowAccountPopup(true);
            }}
            className="account-button"
          >
            Account
          </a>
        </>
      ) : (
        <>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setShowLoginPopup(true);
            }}
            className="account-link"
          >
            Log In
          </a>
          <span className="separator">|</span>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setShowSignupPopup(true);
            }}
            className="account-link"
          >
            Sign Up
          </a>
        </>
      )}

      {showAccountPopup && loggedIn && (
        <AccountPopup
          onClose={() => setShowAccountPopup(false)}
          onLogout={() => {
            localStorage.removeItem('access_token');
            setLoggedIn(false);
            setUsername('');
          }}
          username={username}
        />
      )}
      {showLoginPopup && !loggedIn && (
        <LoginPopup
          onClose={() => setShowLoginPopup(false)}
          onLogin={(data) => {
            localStorage.setItem('access_token', data.access_token);
            setLoggedIn(true);
            setUsername(data.email);
            setShowLoginPopup(false);
          }}
        />
      )}
      {showSignupPopup && !loggedIn && (
        <SignupPopup
          onClose={() => setShowSignupPopup(false)}
          onSignup={(data) => {
            localStorage.setItem('access_token', data.access_token);
            setLoggedIn(true);
            setUsername(data.email);
            setShowSignupPopup(false);
          }}
        />
      )}
    </div>
  );
}
