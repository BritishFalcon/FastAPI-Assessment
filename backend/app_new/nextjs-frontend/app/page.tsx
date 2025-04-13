'use client';

import React from 'react';
import dynamic from "next/dynamic";

const Header = dynamic(() => import('../components/ui/Header'),
    { ssr: false });

const MapView = dynamic(() => import('../components/ui/Map'),
    { ssr: false });

export default function HomePage() {
  return (
    <>
      <Header />
      <MapView />
    </>
  );
}
