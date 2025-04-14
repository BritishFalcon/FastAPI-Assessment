'use client';

import React from 'react';
import dynamic from "next/dynamic";

const MapProvider = dynamic(() => import('../components/context/MapProvider'),
    { ssr: false });

const Header = dynamic(() => import('../components/ui/Header'),
    { ssr: false });

const MapView = dynamic(() => import('../components/ui/Map'),
    { ssr: false });

const AIChat = dynamic(() => import('../components/ui/AIChat'),
    { ssr: false });

export default function HomePage() {
  return (
      <MapProvider>
        <div className="flex flex-col h-screen overflow-hidden">
          {/* Header */}
          <div className="h-16 bg-gray-200 flex-shrink-0">
            <Header />
          </div>

          {/* Content Area */}
          <div className="flex flex-1 min-h-0">
            {/* Sidebar - AIChat */}
            <div className="w-80 bg-white overflow-auto">
              <AIChat />
            </div>

            {/* Map Area */}
            <div className="flex-1 relative overflow-hidden">
              <MapView />
            </div>
          </div>
        </div>
      </MapProvider>
  );
}
