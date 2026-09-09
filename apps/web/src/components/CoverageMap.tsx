"use client";

/**
 * The partner network on a real map of India.
 *
 * Every marker sits at the branch's own latitude and longitude out of the PostGIS
 * registry — this is the partner directory drawn geographically, not a decorative
 * illustration with a `STATE_HOTSPOTS` constant behind it. That distinction is the whole
 * reason the map is worth having: the interesting thing a citizen learns from it is where
 * the network *is not*, and a hand-drawn map cannot show an absence it was never given.
 *
 * Leaflet and its ~150KB arrive through a dynamic import from the coverage page, so a
 * citizen who never opens the map never pays for it — which on 2G is the difference
 * between usable and not. The same component and the same trade already serve
 * `/results/[scheme]/partners`.
 *
 * BOUNDARIES. The tiles are OpenStreetMap's, which draws the northern borders by
 * international convention rather than as the Survey of India does. On a page carrying a
 * ministry's name inside India that is a real problem and not a styling preference — see
 * `TILES` below, which is the single constant to change.
 *
 * The map is `aria-hidden`. The list beside it carries the same partners in text, with
 * their type, district and authorisations; a screen-reader user gets that rather than a
 * pile of unlabelled pins.
 */

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";

import type { DirectoryPartner } from "@/lib/citizenApi";

/**
 * Swap this for a Survey of India / Bhuvan endpoint before this is shown to a ministry.
 * OSM is correct enough for a demo and wrong in exactly the way an Indian government
 * reviewer will notice first.
 */
const TILES = {
  url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
};

/** Mainland plus the island territories, so the default view is the whole country. */
const INDIA: L.LatLngBoundsExpression = [
  [6.5, 68.1],
  [35.7, 97.4],
];

// Leaflet's default marker images resolve relative to the CSS and break under a bundler.
// A tiny inline SVG avoids the asset round-trip entirely.
function pin(selected: boolean) {
  const fill = selected ? "#F59E0B" : "#173B6C";
  return L.divIcon({
    className: "",
    html: `<svg width="26" height="34" viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 0C6.3 0 0 6.3 0 14c0 10 14 22 14 22s14-12 14-22c0-7.7-6.3-14-14-14z" fill="${fill}"/>
      <circle cx="14" cy="14" r="5" fill="#fff"/></svg>`,
    iconSize: [26, 34],
    iconAnchor: [13, 34],
    popupAnchor: [0, -32],
  });
}

/** Frames whatever is on screen: the chosen state's branches, or the country. */
function Frame({ partners }: { partners: DirectoryPartner[] }) {
  const map = useMap();

  useEffect(() => {
    const points = partners
      .filter((partner) => partner.lat !== null && partner.lng !== null)
      .map((partner) => [partner.lat!, partner.lng!] as [number, number]);

    if (points.length === 0) {
      map.fitBounds(INDIA, { padding: [20, 20] });
      return;
    }
    // A single branch has no extent, so `fitBounds` would zoom to the maximum. Pad it
    // into a neighbourhood-sized box instead.
    map.fitBounds(L.latLngBounds(points).pad(points.length === 1 ? 4 : 0.2));
  }, [map, partners]);

  return null;
}

export default function CoverageMap({
  partners,
  selectedId = null,
  onSelect,
}: {
  partners: DirectoryPartner[];
  selectedId?: string | null;
  onSelect?: (partnerId: string) => void;
}) {
  return (
    <MapContainer
      bounds={INDIA}
      scrollWheelZoom={false}
      /* `isolate` is load-bearing. Leaflet stacks its own panes, controls and popups
         between z-index 400 and 1000, and without a stacking context of its own those
         numbers compete in the *page's* root context — where they beat anything the app
         puts at Tailwind's `z-50`. The judge walkthrough was rendering underneath the
         map on the partners step. One property here, rather than an arms race of
         z-indexes everywhere else. */
      className="isolate h-[26rem] w-full rounded-card"
      aria-hidden="true"
    >
      <TileLayer attribution={TILES.attribution} url={TILES.url} />
      <Frame partners={partners} />
      {partners.map((partner) =>
        partner.lat === null || partner.lng === null ? null : (
          <Marker
            key={partner.partner_id}
            position={[partner.lat, partner.lng]}
            icon={pin(partner.partner_id === selectedId)}
            eventHandlers={{ click: () => onSelect?.(partner.partner_id) }}
          >
            <Popup>
              <strong>{partner.name}</strong>
              <br />
              {partner.district}, {partner.state}
            </Popup>
          </Marker>
        ),
      )}
    </MapContainer>
  );
}
