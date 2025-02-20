var map = L.map('map').setView([53.226925, -0.547888], 15);
var img = L.imageOverlay('', [[0, 0], [0, 0]]).addTo(map); // Placeholder for map image to be added to later

host_ip = window.location.hostname;
host_ip = "localhost";
const ac_ws = new WebSocket(`ws://${host_ip}:8000/ws/aircraft`);
var ac_icon = L.icon({ iconUrl: '/static/resources/plane-icon-blue.png', iconSize: [32, 32], iconAnchor: [16, 16] });
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
        ac.remove();
    });

    // Add the new ones
    console.log(data);
    // e.g
    // {"ac": [{"hex": "407569", "type": "adsb_icao", "flight": "EZY27HA ", "r": "G-UZHJ", "t": "A20N", "desc": "AIRBUS A-320neo", "alt_baro": 32950, "alt_geom": 32975, "gs": 485.2, "ias": 262, "tas": 424, "mach": 0.74, "wd": 265, "ws": 65, "oat": -57, "tat": -33, "track": 107.39, "track_rate": 0.03, "roll": -0.53, "mag_heading": 109.86, "true_heading": 110.66, "baro_rate": 384, "geom_rate": 416, "squawk": "6325", "emergency": "none", "category": "A3", "nav_qnh": 1012.8, "nav_altitude_mcp": 32992, "lat": 53.241577, "lon": -0.357291, "nic": 8, "rc": 186, "seen_pos": 0.001, "recentReceiverIds": ["f35129cb-5bca-472d", "15c9c11e-45ed-4f5a", "ece162e7-2441-40be", "db1ef118-aee4-4ee5", "38529bf1-0015-4768", "e51a69be-2973-4120", "2354db8f-afea-4070", "16c7268e-0b3a-4d78", "857aba4f-34b3-df84", "277769b2-14dd-4d0f", "f6f0d202-a915-4970", "72a1e223-cf13-46c3", "58570233-e391-c3ab", "75e76f1d-7f07-4d05", "9e6c1ce2-ed27-4f10", "fee7bbef-12cd-4ab1", "8921ba36-a5ac-4159", "539a55b8-8f11-4613", "461f38c4-4462-4f46", "aa0aa8bc-dec9-4052", "c766baf8-9b4f-4cd7", "43708c49-a11b-45dd", "1a45d513-2f0e-4d1b", "545a6fd6-ed3d-4c77", "76d54db0-c80b-49be", "b3387654-d6c6-42ab", "81183f86-4aba-4497", "945e4e23-48bf-47e4", "17173979-3681-4f1b", "19a1155e-bb7c-436c", "23ef8d7b-ab4e-4d07", "052d20e7-7829-4bf8", "fdd6918a-9277-4b5e", "0e06d0f2-8745-422f", "ab4fe68d-54ef-4daa", "d06cf5b4-92d7-4c41", "95afed4d-42bb-42e7", "852305cb-013e-4a3b", "26a77ae5-a523-4188", "46d6cd38-123d-18df"], "version": 2, "nic_baro": 1, "nac_p": 9, "nac_v": 1, "sil": 3, "sil_type": "perhour", "gva": 2, "sda": 3, "alert": 0, "spi": 0, "mlat": [], "tisb": [], "messages": 975712, "seen": 0.0, "rssi": -11.2, "dst": 8.517, "dir": 65.9}], "msg": "No error", "now": 1739991739001, "total": 1, "ctime": 1739991739001, "ptime": 0}

    var ac_array = data.ac;
    console.log(ac_array);

    for (var i = 0; i < ac_array.length; i++) {
        var aircraft = ac_array[i];
        var lat = aircraft.lat
        var lon = aircraft.lon
        var rot = aircraft.track
        var ac_marker = L.marker([lat, lon], { icon: ac_icon, rotationAngle: rot }).addTo(map);
        ac_instances.push(ac_marker);
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