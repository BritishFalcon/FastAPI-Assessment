var map = L.map('map').setView([53.226925, -0.547888], 15);
var img = L.imageOverlay('', [[0, 0], [0, 0]]).addTo(map); // Placeholder for map image to be added to later

host_ip = window.location.hostname;
const ac_ws = new WebSocket(`ws://${host_ip}:8000/ws/aircraft`);
var ac_icon_default = L.icon({ iconUrl: '/static/resources/plane-icon-blue.png', iconSize: [32, 32], iconAnchor: [16, 16] });
var ac_icon_hover = L.icon({ iconUrl: '/static/resources/plane-icon-yellow.png', iconSize: [32, 32], iconAnchor: [16, 16] });
var ac_instances = [];

// Fetch and update the stitched map image based on current bounds
function getMap() {
    var bounds = map.getBounds();
    var sw = bounds.getSouthWest();
    var ne = bounds.getNorthEast();

    // Construct the URL with query parameters and a cache-busting timestamp
    var url = `/map?sw_lat=${sw.lat}&sw_lon=${sw.lng}&ne_lat=${ne.lat}&ne_lon=${ne.lng}`;

    fetch(url).then(function(response) {

        // sw_lon,sw_lat,ne_lon,ne_lat
        var extentHeader = response.headers.get("Extent");
        var parts = extentHeader.split(",").map(Number);

        // Leaflet is expecting the following format: [[sw_lat, sw_lon], [ne_lat, ne_lon]]
        // Incoming image will use tile coordinates that expand beyond requested bounds, so need to place accordingly.
        var imageBounds = [[parts[1], parts[0]], [parts[3], parts[2]]];

        return response.blob().then(function(blob) {
            return { blob: blob, imageBounds: imageBounds };
        });

    })

    // https://stackoverflow.com/questions/60382263/how-to-avoid-flickering-in-leaflet-tile-layer-wms-implementation
    .then(function(data) {
        var imgURL = URL.createObjectURL(data.blob);
        img.setUrl(imgURL);
        img.setBounds(data.imageBounds);
    });
}

function ac_send_bounds() {
    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const message = JSON.stringify({ sw_lat: sw.lat, sw_lon: sw.lng, ne_lat: ne.lat, ne_lon: ne.lng });
    ac_ws.send(message);
}

ac_ws.onopen = function() { ac_send_bounds(); };

ac_ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Rather than leveraging previous information, this retains an O(n) operation whereas checking would increase
    // the complexity to O(n^2) without the use of a hashmap, which seems a bit OT

    // Remove all the old ones
    ac_instances.forEach(function(ac) {
        ac.marker.remove();
        ac.label.remove();
    });
    ac_instances = [];

    for (var i = 0; i < data.ac.length; i++) {
        var aircraft = data.ac[i];
        var ac_marker = L.marker([aircraft.lat, aircraft.lon], {
            icon: ac_icon_default, rotationAngle: aircraft.track
            }).addTo(map);
        ac_marker.hex = aircraft.hex;

        const flight_label = L.divIcon({
            className: 'flight-label',
            html: aircraft.flight,
            iconSize: [32, 32],
            iconAnchor: [16, -8]
        });

        const label_marker = L.marker([aircraft.lat, aircraft.lon], { icon: flight_label }).addTo(map);

        ac_marker.on('mouseover', function() {
            this.setIcon(ac_icon_hover);
        });

        ac_marker.on('mouseout', function() {
            this.setIcon(ac_icon_default);
        });

        ac_marker.on('click', function(e) {
            const hex = e.target.hex;
            const url = `/hex?hex=${hex}`;

            fetch(url)
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    let details = '';

                    // If "image" in data pop it (it's a URL) and display it at the top of the popup
                    if (data.image) {
                        details += `<img src="${data.image}" alt="Aircraft image" style="max-width:100%; display:block; margin-bottom:10px;">`;
                    }

                    for (const key in data) {
                        if (data.hasOwnProperty(key)) {
                            if (key === 'image') continue;
                            let value = data[key];
                            if (value !== null) {
                                details += `<strong>${key}:</strong> ${value}<br>`;
                            }
                        }
                    }
                    // Optionally add a link for more details
                    details += `<a href="/hex/${hex}" target="_blank">More details</a>`;

                    // Create a popup with an offset so that it appears away from the marker
                    L.popup({
                        offset: L.point(0, -50), // adjust vertical offset as needed
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
    }
}

ac_ws.onclose = function() {
    ac_ws.close();
}

// Send bounds every second (200 added to not hit rate limit)
setInterval(ac_send_bounds, 1200);

// Only update when movement stops else an enormous number of requests are made
map.on('moveend', getMap);

// Initial map load
getMap();