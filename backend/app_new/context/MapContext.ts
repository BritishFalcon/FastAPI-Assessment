import { createContext, useContext } from 'react';
import type L from 'leaflet';

interface MapContextType {
  map: L.Map | null;
  setMap: (map: L.Map | null) => void;
  bounds: L.LatLngBounds | null;
  setBounds: (bounds: L.LatLngBounds | null) => void;
}

export const MapContext = createContext<MapContextType | null>(null);

export const useMapContext = () => {
  const ctx = useContext(MapContext);
  if (!ctx) throw new Error('useMapContext must be used within a MapProvider');
  return ctx;
};
