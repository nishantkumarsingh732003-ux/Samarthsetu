"use client";

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";

import type { RoutedPartner } from "@/lib/api";

/**
 * OSM map of routable partners.
 *
 * Loaded only via a dynamic import from the partners page, so Leaflet's ~150KB never
 * enters the citizen route's initial bundle. A citizen who never opens the map never
 * pays for it — which on 2G is the difference between usable and not.
 */

// Leaflet's default marker images resolve relative to the CSS and break under a
// bundler. A tiny inline SVG avoids the asset round-trip entirely.
const icon = L.divIcon({
  className: "",
  html: `<svg width="28" height="36" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 0C6.3 0 0 6.3 0 14c0 10 14 22 14 22s14-12 14-22c0-7.7-6.3-14-14-14z" fill="#0E4266"/>
    <circle cx="14" cy="14" r="5" fill="#fff"/></svg>`,
  iconSize: [28, 36],
  iconAnchor: [14, 36],
  popupAnchor: [0, -34],
});

export default function PartnerMap({
  origin,
  partners,
}: {
  origin: { lat: number; lng: number } | null;
  partners: RoutedPartner[];
}) {
  const centre = origin ?? { lat: 21.1458, lng: 79.0882 };

  return (
    <MapContainer
      center={[centre.lat, centre.lng]}
      zoom={11}
      scrollWheelZoom={false}
      className="h-72 w-full rounded-card"
      // The map is decorative relative to the list beneath it, which carries the same
      // information in text. Screen-reader users get the list, not a pile of markers.
      aria-hidden="true"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {partners.map((partner) =>
        partner.lat === null || partner.lng === null ? null : (
          <Marker key={partner.partner_id} position={[partner.lat, partner.lng]} icon={icon}>
            <Popup>
              <strong>{partner.name}</strong>
              <br />
              {partner.district}
            </Popup>
          </Marker>
        ),
      )}
    </MapContainer>
  );
}
