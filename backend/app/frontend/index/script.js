var map = L.map('map').setView([53.226925, -0.547888], 15);
var img = L.imageOverlay('', [[0, 0], [0, 0]]).addTo(map); // Placeholder for map image to be added to later

// Fetch and update the stitched map image based on current bounds
function getMap() {
    var bounds = map.getBounds();
    var sw = bounds.getSouthWest();
    var ne = bounds.getNorthEast();

    // Construct the URL with query parameters and a cache-busting timestamp
    var url = `/map?sw_lat=${sw.lat}&sw_lon=${sw.lng}&ne_lat=${ne.lat}&ne_lon=${ne.lng}&t=${Date.now()}`;

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

// Only update when movement stops else an enormous number of requests are made
map.on('moveend', getMap);

// Initial map load
getMap();