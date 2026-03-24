import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';


delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});


function EventLocationMap({ latitude, longitude }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || latitude == null || longitude == null) {
      return undefined;
    }

    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current, {
        zoomControl: false,
        dragging: true,
        scrollWheelZoom: false,
      }).setView([latitude, longitude], 15);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(mapInstance.current);
    } else {
      mapInstance.current.setView([latitude, longitude], 15);
    }

    if (!markerRef.current) {
      markerRef.current = L.marker([latitude, longitude]).addTo(mapInstance.current);
    } else {
      markerRef.current.setLatLng([latitude, longitude]);
    }

    return () => {};
  }, [latitude, longitude]);

  useEffect(() => {
    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove();
        mapInstance.current = null;
      }
    };
  }, []);

  if (latitude == null || longitude == null) {
    return null;
  }

  return <div ref={mapRef} className="h-64 w-full rounded-2xl border border-gray-200 overflow-hidden" />;
}


export default EventLocationMap;
