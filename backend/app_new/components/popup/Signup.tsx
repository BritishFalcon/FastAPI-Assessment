'use client';
import React, { useState } from 'react';
import '../Account.module.css';

interface SignupPopupProps {
  onClose: () => void;
  onSignup: (data: { access_token: string; email: string }) => void;
}

export default function SignupPopup({ onClose, onSignup }: SignupPopupProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSignup = async () => {
    const signupURL = `/signup?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
    const response = await fetch(signupURL, { method: 'POST' });
    if (response.ok) {
      const data = await response.json();
      onSignup(data);
    } else {
      const error = await response.text();
      alert(error);
    }
  };

  return (
    <div className="popup-overlay" id="signup-popup" style={{ display: 'block' }}>
      <div className="popup-content">
        <span className="close" onClick={onClose}>
          &times;
        </span>
        <h2>Sign Up</h2>
        <input
          type="text"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleSignup}>Sign Up</button>
      </div>
    </div>
  );
}
