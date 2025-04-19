'use client';
import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet-rotatedmarker';
import 'leaflet/dist/leaflet.css';
import {MapContext, useMapContext} from '@/context/MapContext';

const Map = () => {
  const mapContainer = useRef(null);
  const { map, setMap, bounds, setBounds } = useMapContext();

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = L.map(mapContainer.current).setView([53.226925, -0.547888], 15);
    setMap(map);

    const img = L.imageOverlay('', [[0, 0], [0, 0]]).addTo(map);
    const host_ip = window.location.hostname;
    const ac_ws = new WebSocket(`/ws/aircraft`);

    const ac_icon_default = L.icon({ iconUrl: '/images/plane-icon-blue.png', iconSize: [32, 32], iconAnchor: [16, 16] });
    const ac_icon_hover = L.icon({ iconUrl: '/images/plane-icon-yellow.png', iconSize: [32, 32], iconAnchor: [16, 16] });
    let ac_instances = [];

    function getMap() {
      const bounds = map.getBounds();
      setBounds(bounds);

      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();

      fetch(`/map/?sw_lat=${sw.lat}&sw_lon=${sw.lng}&ne_lat=${ne.lat}&ne_lon=${ne.lng}`)
        .then((res) => {
          const extentHeader = res.headers.get("Extent");
          const parts = extentHeader.split(",").map(Number);
          const imageBounds = [[parts[1], parts[0]], [parts[3], parts[2]]];
          return res.blob().then((blob) => ({ blob, imageBounds }));
        })
        .then(({ blob, imageBounds }) => {
          const imgURL = URL.createObjectURL(blob);
          img.setUrl(imgURL);
          img.setBounds(imageBounds);
        })
        .catch((err) => console.error("Error fetching map image:", err));
    }

    function ac_send_bounds() {
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      const message = JSON.stringify({ sw_lat: sw.lat, sw_lon: sw.lng, ne_lat: ne.lat, ne_lon: ne.lng });
      ac_ws.send(message);
    }

    ac_ws.onopen = () => ac_send_bounds();

    ac_ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      ac_instances.forEach(({ marker, label }) => {
        marker.remove();
        label.remove();
      });
      ac_instances = [];

      data.ac.forEach((aircraft) => {
        const ac_marker = L.marker([aircraft.lat, aircraft.lon], {
          icon: ac_icon_default,
          rotationAngle: aircraft.track,
        }).addTo(map);
        ac_marker.hex = aircraft.hex;

        const flight_label = L.divIcon({
          className: 'flight-label',
          html: aircraft.flight,
          iconSize: [32, 32],
          iconAnchor: [16, -8]
        });
        const label_marker = L.marker([aircraft.lat, aircraft.lon], { icon: flight_label }).addTo(map);

        ac_marker.on('mouseover', () => ac_marker.setIcon(ac_icon_hover));
        ac_marker.on('mouseout', () => ac_marker.setIcon(ac_icon_default));
        ac_marker.on('click', (e) => {
          const hex = e.target.hex;
          fetch(`/adsb/hex?hex=${hex}`)
            .then((res) => res.json())
            .then((data) => {
              let details = '';
              for (let key in data) {
                if (data[key] == null) continue;
                details += `<strong>${key}:</strong> ${data[key]}<br>`;
              }

              const popup = L.popup({offset: L.point(0, -50), autoPan: true})
                  .setLatLng(e.latlng)
                  .setContent(details)
                  .openOn(map);

              // Doing this separately, getting image via API is just too slow for a usable UX
              fetch(`/adsb/hex?hex=${hex}&image=true`)
                  .then(r => r.json())
                  .then(data => {
                    if (data.image) {
                      const img = `<img src="${data.image}" alt="Aircraft Image" style="width: 200px; height: auto;">`;
                      popup.setContent(img + details);
                      popup.update();
                    }
                  });
              });
        });

        ac_instances.push({ marker: ac_marker, label: label_marker });
      });
    };

    ac_ws.onclose = () => ac_ws.close();

    const intervalId = setInterval(ac_send_bounds, 1200);
    map.on('moveend', getMap);
    getMap();

    return () => {
      clearInterval(intervalId);
      map.off('moveend', getMap);
      setMap(null);
      setBounds(null);
      ac_ws.close();
      map.remove();
    };
  }, [mapContainer, setMap]);

  return (
    <MapContext.Provider value={{ map, setMap, bounds, setBounds }}>
      <div id="map" ref={mapContainer} style={{ width: '100%', height: '100vh' }} />
    </MapContext.Provider>
  );
};

export default Map;
