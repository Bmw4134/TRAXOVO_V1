
// Mapbox-style job zone refresh script
function updateMapWithZones(data) {
  data.forEach(zone => {
    addMapPin(zone.lat, zone.lon, zone.name, zone.activeDrivers);
  });
}
