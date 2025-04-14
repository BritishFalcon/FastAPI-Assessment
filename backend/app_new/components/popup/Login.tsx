'use client';
import React, { useState } from 'react';
import '../Account.module.css';

interface LoginPopupProps {
  onClose: () => void;
  onLogin: (data: { access_token: string; email: string }) => void;
}

export default function LoginPopup({ onClose, onLogin }: LoginPopupProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    const loginURL = `/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
    const response = await fetch(loginURL, { method: 'POST' });
    if (response.ok) {
      const data = await response.json();
      onLogin(data);
    } else {
      const error = await response.text();
      alert(error);
    }
  };

  return (
    <div className="popup-overlay" id="leaflet-popup" style={{ display: 'block' }}>
      <div className="popup-content">
        <span className="close" onClick={onClose}>
          &times;
        </span>
        <h2>Login</h2>
        <input
          type="text"
          placeholder="Username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button onClick={handleLogin}>Login</button>
      </div>
    </div>
  );
}
