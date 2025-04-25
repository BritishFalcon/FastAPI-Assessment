'use client';
import React, { useEffect, useState } from 'react';
import Popup from 'reactjs-popup';
import 'reactjs-popup/dist/index.css';

export default function AccountArea() {
  // Bootstrap the token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const [authChecked, setAuthChecked] = useState(false);
  const [loggedIn, setLoggedIn] = useState(!!token);
  const [username, setUsername] = useState('');

  // Manage which popup is open
  const [popupType, setPopupType] = useState<'login' | 'signup' | 'account' | null>(null);

  useEffect(() => {
    // If a token exists, try to validate it
    if (token) {
      fetch(`/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
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
  }, [token]);

  if (!authChecked) {
    return (
      <div className="account">
        <a href="#" className="account-link">Log In</a>
        <span className="separator">|</span>
        <a href="#" className="account-link">Sign Up</a>
      </div>
    );
  }

  const openPopup = (type: 'login' | 'signup' | 'account') => (e: React.MouseEvent) => {
    e.preventDefault();
    setPopupType(type);
  };

  const closePopup = () => {
    setPopupType(null);
  };

  const handleLogin = async (email: string, password: string) => {
    try {
      const loginURL = `/auth/login`;
      const body = new URLSearchParams({ username: email, password }).toString();
      const response = await fetch(loginURL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body,
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        setLoggedIn(true);
        setUsername(data.email);
        closePopup();
        window.location.reload();
      } else {
        const error = await response.text();
        alert(error);
      }
    } catch (err) {
      console.error('Login error:', err);
    }
  };

  const handleSignup = async (email: string, password: string) => {
    try {
      const signupURL = `/auth/register`;
      const response = await fetch(signupURL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        setLoggedIn(true);
        setUsername(data.email);
        closePopup();
        window.location.reload();
      } else {
        const error = await response.text();
        alert(error);
      }
    } catch (err) {
      console.error('Signup error:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setLoggedIn(false);
    setUsername('');
    closePopup();
  };

  return (
    <div className="account">
      {loggedIn ? (
        <>
          <span className="username-display">{username}</span>
          <a href="#" onClick={openPopup('account')} className="account-button">
            &nbsp;Account
          </a>
        </>
      ) : (
        <>
          <a href="#" onClick={openPopup('login')} className="account-link">
            &nbsp;Log In&nbsp;
          </a>
          <span className="separator">|</span>
          <a href="#" onClick={openPopup('signup')} className="account-link">
            &nbsp;Sign Up
          </a>
        </>
      )}

      {/* Popup for Login */}
      <Popup open={popupType === 'login'} onClose={closePopup} modal nested>
        <div className="popup-content">
          <span className="close" onClick={closePopup}>&times;</span>
          <h2>Login</h2>
          <LoginForm onLogin={handleLogin} />
        </div>
      </Popup>

      {/* Popup for Signup */}
      <Popup open={popupType === 'signup'} onClose={closePopup} modal nested>
        <div className="popup-content">
          <span className="close" onClick={closePopup}>&times;</span>
          <h2>Sign Up</h2>
          <SignupForm onSignup={handleSignup} />
        </div>
      </Popup>

      {/* Popup for Account Details */}
      <Popup open={popupType === 'account'} onClose={closePopup} modal nested>
        <div className="popup-content">
          <span className="close" onClick={closePopup}>&times;</span>
          <h2>Account Details</h2>
          <p className="popup-email">Username: {username}</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </Popup>
    </div>
  );
}

// Minimal login form component
function LoginForm({ onLogin }: { onLogin: (email: string, password: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <>
      <input type="text" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={() => onLogin(email, password)}>Login</button>
    </>
  );
}

// Minimal signup form component
function SignupForm({ onSignup }: { onSignup: (email: string, password: string) => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  return (
    <>
      <input type="text" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={() => onSignup(email, password)}>Sign Up</button>
    </>
  );
}
