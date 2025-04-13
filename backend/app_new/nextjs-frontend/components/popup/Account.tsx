'use client';
import React from 'react';
import '../Account.module.css';

interface AccountPopupProps {
  onClose: () => void;
  onLogout: () => void;
  username: string;
}

export default function AccountPopup({ onClose, onLogout, username }: AccountPopupProps) {
  return (
    <div className="popup-overlay" id="account-popup" style={{ display: 'block' }}>
      <div className="popup-content">
        <span className="close" onClick={onClose}>
          &times;
        </span>
        <h2>Account Details</h2>
        <p className="popup-email">Username: {username}</p>
        <button onClick={onLogout}>Logout</button>
      </div>
    </div>
  );
}
