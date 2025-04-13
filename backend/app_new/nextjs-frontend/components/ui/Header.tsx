'use client';
import React from 'react';
import AccountArea from './AccountArea';
import './Header.module.css';

export default function Header() {
  return (
    <header className="header">
      <div className="header-left">
        <h1>FastAPI Aviation Map</h1>
      </div>
      <div className="header-center">
        <input
          type="text"
          className="search-bar"
          placeholder="Search for flights, airports..."
        />
      </div>
      <div className="header-right">
        <AccountArea />
      </div>
    </header>
  );
}