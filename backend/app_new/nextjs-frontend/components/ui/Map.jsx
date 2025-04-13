import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet-rotatedmarker';
import 'leaflet/dist/leaflet.css';

const Map = () => {
  const mapContainer = useRef(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    var map = L.map(mapContainer.current).setView([53.226925, -0.547888], 15);
    var img = L.imageOverlay('', [[0, 0], [0, 0]]).addTo(map); // Placeholder for map image

    var host_ip = window.location.hostname;
    var ac_ws = new WebSocket(`ws://${host_ip}:8000/ws/aircraft`);
    var ac_icon_default = L.icon({
      iconUrl: '/images/plane-icon-blue.png',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
    var ac_icon_hover = L.icon({
      iconUrl: '/images/plane-icon-yellow.png',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
    var ac_instances = [];

    // Fetch and update the stitched map image based on current bounds
    function getMap() {
      var bounds = map.getBounds();
      var sw = bounds.getSouthWest();
      var ne = bounds.getNorthEast();
      var url = `http://${host_ip}:8000/map?sw_lat=${sw.lat}&sw_lon=${sw.lng}&ne_lat=${ne.lat}&ne_lon=${ne.lng}`;

      fetch(url)
        .then(function(response) {
          var extentHeader = response.headers.get("Extent");
          var parts = extentHeader.split(",").map(Number);
          var imageBounds = [[parts[1], parts[0]], [parts[3], parts[2]]];
          return response.blob().then(function(blob) {
            return { blob: blob, imageBounds: imageBounds };
          });
        })
        .then(function(data) {
          var imgURL = URL.createObjectURL(data.blob);
          img.setUrl(imgURL);
          img.setBounds(data.imageBounds);
        })
        .catch(function(err) {
          console.error("Error fetching map image:", err);
        });
    }

    function ac_send_bounds() {
      var bounds = map.getBounds();
      var sw = bounds.getSouthWest();
      var ne = bounds.getNorthEast();
      var message = JSON.stringify({
        sw_lat: sw.lat,
        sw_lon: sw.lng,
        ne_lat: ne.lat,
        ne_lon: ne.lng,
      });
      ac_ws.send(message);
    }

    ac_ws.onopen = function() { ac_send_bounds(); };

    ac_ws.onmessage = function(event) {
      var data = JSON.parse(event.data);

      ac_instances.forEach(function(ac) {
        ac.marker.remove();
        ac.label.remove();
      });
      ac_instances = [];

      data.ac.forEach(function(aircraft) {
        var ac_marker = L.marker([aircraft.lat, aircraft.lon], {
          icon: ac_icon_default,
          rotationAngle: aircraft.track // This relies on leaflet.rotatedMarker.js being loaded somewhere
        }).addTo(map);
        ac_marker.hex = aircraft.hex;

        var flight_label = L.divIcon({
          className: 'flight-label',
          html: aircraft.flight,
          iconSize: [32, 32],
          iconAnchor: [16, -8]
        });
        var label_marker = L.marker([aircraft.lat, aircraft.lon], { icon: flight_label }).addTo(map);

        ac_marker.on('mouseover', function() {
          this.setIcon(ac_icon_hover);
        });
        ac_marker.on('mouseout', function() {
          this.setIcon(ac_icon_default);
        });
        ac_marker.on('click', function(e) {
          var hex = e.target.hex;
          var url = `http://${host_ip}:8000/hex?hex=${hex}`;

          fetch(url)
            .then(function(response) {
              return response.json();
            })
            .then(function(data) {
              var details = '';
              if (data.image) {
                details += `<img src="${data.image}" alt="Aircraft image" style="max-width:100%; display:block; margin-bottom:10px;">`;
              }
              for (var key in data) {
                if (data.hasOwnProperty(key)) {
                  if (key === 'image') continue;
                  var value = data[key];
                  if (value !== null) {
                    details += `<strong>${key}:</strong> ${value}<br>`;
                  }
                }
              }
              details += `<a href="/hex/${hex}" target="_blank">More details</a>`;

              L.popup({
                offset: L.point(0, -50),
                autoPan: true
              })
              .setLatLng(e.latlng)
              .setContent(details)
              .openOn(map);
            })
            .catch(function(error) {
              console.error('Error fetching data for hex', hex, error);
            });
        });

        ac_instances.push({ marker: ac_marker, label: label_marker });
      });
    };

    ac_ws.onclose = function() {
      ac_ws.close();
    };

    var intervalId = setInterval(ac_send_bounds, 1200);
    map.on('moveend', getMap);
    getMap();

    return () => {
      clearInterval(intervalId);
      map.off('moveend', getMap);
      ac_ws.close();
      map.remove();
    };
  }, []);

  return (
    <div id="map" ref={mapContainer} style={{ width: '100%', height: '100vh' }} />
  );
};

export default Map;
