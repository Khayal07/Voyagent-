import L from "leaflet";
import { useReducedMotion } from "motion/react";
import { useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { useT } from "../i18n";
import type { LivePoint } from "../hooks/useLivePoints";
import type { Itinerary } from "../types";
import PoiThumb from "./PoiThumb";

// Gün palitrası — işıqlı xəritədə oxunan tünd tonlar; HUD/ItineraryPanel ilə paylaşılır
export const DAY_COLORS = ["#9a6a10", "#33568f", "#7b4bab", "#1f7a4d", "#b03052"];

const TILE_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

// isNew: marker ilk dəfə görünür — yumşaq düşmə (geo-drop)
function numberIcon(color: string, n: number, isNew: boolean) {
  const pin =
    `<div class="${isNew ? "geo-drop" : ""}" style="background:${color};color:#fff;width:26px;height:26px;border-radius:50% 50% 50% 0;` +
    `transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;` +
    `border:2px solid #fff;box-shadow:0 1px 4px rgb(15 23 42 / .35)">` +
    `<span style="transform:rotate(45deg);font:600 12px 'IBM Plex Mono',monospace">${n}</span></div>`;
  return L.divIcon({
    className: "",
    html: `<div style="position:relative">${pin}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
  });
}

// Danışıq zamanı düşən aralıq nöqtələr — oxra, nömrəsiz
function liveIcon(isNew: boolean) {
  const dot =
    `<div class="${isNew ? "geo-drop" : ""}" style="width:12px;height:12px;border-radius:50%;background:#9a6a10;` +
    `border:2px solid #fff;box-shadow:0 1px 3px rgb(15 23 42 / .35)"></div>`;
  return L.divIcon({
    className: "",
    html: `<div style="position:relative">${dot}</div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

// Marşrutu "gəzən" canlı marker — nəbz halqalı oxra nöqtə
function travelerIcon() {
  const html =
    `<div class="route-traveler"><span class="route-traveler-ring"></span>` +
    `<span class="route-traveler-dot"></span></div>`;
  return L.divIcon({ className: "", html, iconSize: [22, 22], iconAnchor: [11, 11] });
}

const TRAVELER_ICON = travelerIcon();
const SEGMENT_MS = 850; // hər dayanacaqlar arası keçid müddəti

// Marker-i marşrut boyunca ardıcıl dayanacaqlar arasında animasiya edir;
// arxada "keçilən yol" polilaynı böyüyür. reduced-motion-da dərhal sona atır.
function RoutePlayer({
  points,
  color,
  playing,
  onEnd,
}: {
  points: [number, number][];
  color: string;
  playing: boolean;
  onEnd: () => void;
}) {
  const reduced = useReducedMotion();
  const [pos, setPos] = useState<[number, number] | null>(null);
  const [traveled, setTraveled] = useState<[number, number][]>([]);
  const rafRef = useRef(0);

  useEffect(() => {
    if (!playing || points.length < 2) return;
    if (reduced) {
      setTraveled(points);
      setPos(points[points.length - 1]);
      const id = setTimeout(onEnd, 400);
      return () => clearTimeout(id);
    }
    let seg = 0;
    let start = performance.now();
    setTraveled([points[0]]);
    setPos(points[0]);
    const step = (now: number) => {
      const a = points[seg];
      const b = points[seg + 1];
      const frac = Math.min(1, (now - start) / SEGMENT_MS);
      setPos([a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac]);
      if (frac >= 1) {
        seg += 1;
        setTraveled(points.slice(0, seg + 1));
        start = now;
        if (seg >= points.length - 1) {
          onEnd();
          return;
        }
      }
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, points, reduced]);

  if (!playing || !pos) return null;
  return (
    <>
      {traveled.length > 1 && (
        <Polyline
          positions={traveled}
          pathOptions={{ color, weight: 5, opacity: 0.9 }}
        />
      )}
      <Marker position={pos} icon={TRAVELER_ICON} interactive={false} zIndexOffset={1000} />
    </>
  );
}

function FitBounds({
  points,
  enabledRef,
}: {
  points: [number, number][];
  enabledRef?: RefObject<boolean>;
}) {
  const map = useMap();
  const key = JSON.stringify(points);
  useEffect(() => {
    // Scrubber işə düşəndən sonra kamera ilə "dava etməsin"
    if (enabledRef && !enabledRef.current) return;
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
  currency: string;
  livePoints?: LivePoint[] | null;
  mapRef?: RefObject<L.Map | null>;
  fitEnabledRef?: RefObject<boolean>;
  playing?: boolean; // marşrut animasiyası oynayır
  onPlayEnd?: () => void;
}

export default function MapView({
  center,
  itinerary,
  selectedDay,
  currency,
  livePoints,
  mapRef,
  fitEnabledRef,
  playing = false,
  onPlayEnd,
}: Props) {
  const t = useT();
  const days = itinerary?.days ?? [];

  // Sonar yalnız YENİ adlar üçün: mount anında mövcud olanlar (replay) heç vaxt düşmür,
  // animasiya bitəndən sonra siyahı boşalır ki, filtr re-render-i təkrar düşürməsin.
  const seenRef = useRef<Set<string> | null>(null);
  const [newNames, setNewNames] = useState<Set<string>>(() => new Set());
  const allNames = useMemo(() => {
    const names: string[] = [];
    for (const d of days) for (const i of d.items) names.push(i.name);
    for (const p of livePoints ?? []) names.push(p.name);
    return names;
  }, [days, livePoints]);
  if (seenRef.current === null) seenRef.current = new Set(allNames);
  const namesKey = allNames.join("|");
  useEffect(() => {
    const seen = seenRef.current!;
    const fresh = allNames.filter((n) => !seen.has(n));
    for (const n of fresh) seen.add(n);
    if (fresh.length > 0) {
      setNewNames(new Set(fresh));
      const id = setTimeout(() => setNewNames(new Set()), 1700);
      return () => clearTimeout(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [namesKey]);

  const focusPoints = useMemo<[number, number][]>(() => {
    if (days.length === 0 && livePoints && livePoints.length > 0) {
      return livePoints.map((p) => [p.lat, p.lon] as [number, number]);
    }
    const source = selectedDay === 0 ? days : days.filter((d) => d.day === selectedDay);
    return source.flatMap((d) =>
      d.items
        .filter((i) => i.lat != null && i.lon != null)
        .map((i) => [i.lat!, i.lon!] as [number, number])
    );
  }, [days, selectedDay, livePoints]);

  return (
    <div className="h-full min-h-[300px] overflow-hidden">
      <MapContainer
        ref={mapRef}
        center={center}
        zoom={12}
        className="h-full w-full"
        scrollWheelZoom
        zoomControl={false}
      >
        <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />

        {/* Yekundan əvvəl: son təklifin nöqtələri (qızılı) */}
        {days.length === 0 &&
          livePoints?.map((p, idx) => (
            <Marker key={`live-${p.day}-${idx}-${p.name}`} position={[p.lat, p.lon]} icon={liveIcon(newNames.has(p.name))}>
              <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                <span style={{ font: "500 12px Archivo, sans-serif" }}>{p.name}</span>
              </Tooltip>
            </Marker>
          ))}

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
                pathOptions={{
                  color,
                  weight: 3,
                  opacity: dimmed ? 0.15 : 0.85,
                  className: "route-flow", // axan tirələr — hərəkət istiqaməti nöqtə sırasıdır
                }}
              />
              {d.items
                .filter((i) => i.lat != null && i.lon != null)
                .map((i, idx) => (
                  <Marker
                    key={`${d.day}-${i.name}`}
                    position={[i.lat!, i.lon!]}
                    icon={numberIcon(dimmed ? "#b3bac7" : color, idx + 1, newNames.has(i.name))}
                  >
                    <Tooltip direction="top" offset={[0, -26]} opacity={0.95}>
                      <span style={{ font: "500 12px Archivo, sans-serif" }}>{i.name}</span>
                    </Tooltip>
                    <Popup>
                      <PoiThumb wiki={i.wiki} name={i.name} size={160} />
                      <strong>{i.name}</strong>
                      <br />
                      {t.day} {d.day} · {t.startsAt} {i.start_time ?? "—"}
                      <br />
                      {i.est_cost} {currency} {t.perPerson} · ~{i.duration_min} {t.minutes}
                    </Popup>
                  </Marker>
                ))}
            </div>
          );
        })}
        <RoutePlayer
          points={focusPoints}
          color={DAY_COLORS[(Math.max(1, selectedDay) - 1) % DAY_COLORS.length]}
          playing={playing && focusPoints.length > 1}
          onEnd={() => onPlayEnd?.()}
        />
        <FitBounds
          points={focusPoints.length > 0 ? focusPoints : [center]}
          enabledRef={fitEnabledRef}
        />
      </MapContainer>
    </div>
  );
}
