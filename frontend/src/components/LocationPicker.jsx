import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export default function LocationPicker({ latitude, longitude, onLocationSelect }) {
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const markerInstance = useRef(null);

    useEffect(() => {
        if (!mapRef.current) return;

        // Initialize map only once
        if (!mapInstance.current) {
            const defaultCenter = [27.7172, 85.3240];
            const center = latitude && longitude ? [latitude, longitude] : defaultCenter;

            mapInstance.current = L.map(mapRef.current).setView(center, 13);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(mapInstance.current);

            // Add click listener
            mapInstance.current.on('click', (e) => {
                const { lat, lng } = e.latlng;
                // Round to 6 decimal places to satisfy backend max_digits=9 constraints
                onLocationSelect(Number(lat.toFixed(6)), Number(lng.toFixed(6)));
            });
        }

        // Update marker when props change
        if (latitude && longitude && mapInstance.current) {
            if (markerInstance.current) {
                markerInstance.current.setLatLng([latitude, longitude]);
            } else {
                markerInstance.current = L.marker([latitude, longitude]).addTo(mapInstance.current);
            }
            // Optionally, pan to the new location
            mapInstance.current.panTo([latitude, longitude]);
        }

        return () => {
            // Unmount cleanup: do NOT destroy map on every render to avoid flicker,
            // but if the component truly unmounts, leaflet map should be removed.
            // Vite hot reloading sometimes causes issues here, so we wrap it.
        };
    }, [latitude, longitude]);

    // Handle full cleanup on unmount only
    useEffect(() => {
        return () => {
            if (mapInstance.current) {
                mapInstance.current.remove();
                mapInstance.current = null;
            }
        };
    }, []);

    return (
        <div className="relative h-[300px] w-full rounded-xl overflow-hidden border border-gray-200 z-0">
            <div ref={mapRef} style={{ height: '100%', width: '100%', zIndex: 0 }}></div>
            <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-lg shadow-sm border border-gray-100 text-xs font-medium text-gray-700 pointer-events-none" style={{ zIndex: 400 }}>
                Click anywhere to drop a pin
            </div>
        </div>
    );
}
