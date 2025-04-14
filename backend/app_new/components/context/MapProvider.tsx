'use client';
import React, { useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapContext } from '@/context/MapContext';

const MapProvider = ({ children }: { children: React.ReactNode }) => {
  const [map, setMap] = useState<L.Map | null>(null);
  const [bounds, setBounds] = useState<L.LatLngBounds | null>(null);

  return (
    <MapContext.Provider value={{ map, setMap, bounds, setBounds }}>
      {children}
    </MapContext.Provider>
  );
};

export default MapProvider;
