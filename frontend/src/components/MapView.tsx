import L from "leaflet";
import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import type { Itinerary } from "../types";

export const DAY_COLORS = ["#e4572e", "#2274a5", "#2e933c", "#7c5cbf", "#d98e04"];

const TILE_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

function numberIcon(color: string, n: number) {
  return L.divIcon({
    className: "",
    html:
      `<div style="background:${color};color:#fff;width:26px;height:26px;border-radius:50% 50% 50% 0;` +
      `transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;` +
      `border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)">` +
      `<span style="transform:rotate(45deg);font:600 12px 'IBM Plex Mono',monospace">${n}</span></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  });
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  const key = JSON.stringify(points);
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 15 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, map]);
  return null;
}

interface Props {
  center: [number, number];
  itinerary: Itinerary | null;
  selectedDay: number; // 0 = bütün günlər
}

export default function MapView({ center, itinerary, selectedDay }: Props) {
  const days = itinerary?.days ?? [];

  const focusPoints = useMemo<[number, number][]>(() => {
    const source = selectedDay === 0 ? days : days.filter((d) => d.day === selectedDay);
    return source.flatMap((d) =>
      d.items
        .filter((i) => i.lat != null && i.lon != null)
        .map((i) => [i.lat!, i.lon!] as [number, number])
    );
  }, [days, selectedDay]);

  return (
    <div className="h-[420px] overflow-hidden rounded-lg border border-line">
      <MapContainer center={center} zoom={12} className="h-full w-full" scrollWheelZoom>
        <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
        {days.map((d) => {
          const color = DAY_COLORS[(d.day - 1) % DAY_COLORS.length];
          const dimmed = selectedDay !== 0 && selectedDay !== d.day;
          const points = d.items
            .filter((i) => i.lat != null && i.lon != null)
            .map((i) => [i.lat!, i.lon!] as [number, number]);
          return (
            <div key={d.day}>
              <Polyline
                positions={points}
                pathOptions={{ color, dashArray: "8 8", weight: 3, opacity: dimmed ? 0.2 : 0.9 }}
              />
              {d.items
                .filter((i) => i.lat != null && i.lon != null)
                .map((i, idx) => (
                  <Marker
                    key={`${d.day}-${i.name}`}
                    position={[i.lat!, i.lon!]}
                    icon={numberIcon(dimmed ? "#9fb0ab" : color, idx + 1)}
                  >
                    <Popup>
                      <strong>{i.name}</strong>
                      <br />
                      Gün {d.day} · {i.start_time ?? ""} · {i.est_cost} adambaşı
                    </Popup>
                  </Marker>
                ))}
            </div>
          );
        })}
        <FitBounds points={focusPoints.length > 0 ? focusPoints : [center]} />
      </MapContainer>
    </div>
  );
}
