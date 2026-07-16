import type L from "leaflet";
import { useEffect, useMemo, useRef, useState } from "react";
import type { LiveProposal } from "../hooks/useLivePoints";
import { useT } from "../i18n";
import { budgetFromItinerary, budgetFromLive } from "../lib/budget";
import type { Phase } from "../streamState";
import type { Itinerary, Trip } from "../types";
import BudgetGauge from "./hud/BudgetGauge";
import DayFilterHud from "./hud/DayFilterHud";
import ItineraryDrawer from "./hud/ItineraryDrawer";
import TimelineScrubber, { type ScrubStop } from "./hud/TimelineScrubber";
import MapView from "./MapView";

interface Props {
  trip: Trip;
  phase: Phase;
  itinerary: Itinerary | null;
  live: LiveProposal | null;
  cityCenter: [number, number] | null;
  selectedDay: number;
  onSelectDay: (day: number) => void;
  onItineraryChange: (it: Itinerary) => void;
  onError: (detail: string) => void;
  visible?: boolean; // mobil tab görünəndə Leaflet ölçünü yeniləməlidir
  readOnly?: boolean; // paylaşma görünüşü — drag&drop redaktəsi bağlıdır
}

// Tam-ekran xəritə + üstündə HUD qatı (solid panellər)
export default function MapCanvas({
  trip,
  phase,
  itinerary,
  live,
  cityCenter,
  selectedDay,
  onSelectDay,
  onItineraryChange,
  onError,
  visible = true,
  readOnly = false,
}: Props) {
  const t = useT();
  const mapRef = useRef<L.Map | null>(null);
  const fitEnabledRef = useRef(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [playing, setPlaying] = useState(false);
  const prevPhaseRef = useRef(phase);

  // done fazasına keçəndə drawer avtomatik açılır
  useEffect(() => {
    if (prevPhaseRef.current !== "done" && phase === "done") setDrawerOpen(true);
    prevPhaseRef.current = phase;
  }, [phase]);

  // Gün filtri dəyişəndə FitBounds yenidən aktivləşir və animasiya dayanır
  useEffect(() => {
    fitEnabledRef.current = true;
    setPlaying(false);
  }, [selectedDay, trip.id]);

  // display:none-dan çıxanda (mobil tab) Leaflet konteyner ölçüsünü yenidən oxumalıdır
  useEffect(() => {
    if (!visible) return;
    const id = setTimeout(() => mapRef.current?.invalidateSize(), 60);
    return () => clearTimeout(id);
  }, [visible]);

  // Scrubber üçün xronoloji dayanacaqlar (yekun və ya canlı təklif)
  const stops = useMemo<ScrubStop[]>(() => {
    if (itinerary) {
      const days = selectedDay === 0 ? itinerary.days : itinerary.days.filter((d) => d.day === selectedDay);
      return days.flatMap((d) =>
        d.items
          .filter((i) => i.lat != null && i.lon != null)
          .map((i) => ({ name: i.name, lat: i.lat!, lon: i.lon!, day: d.day })),
      );
    }
    return (live?.points ?? []).map((p) => ({ name: p.name, lat: p.lat, lon: p.lon, day: p.day }));
  }, [itinerary, live, selectedDay]);

  const alloc = useMemo(() => {
    if (itinerary) return budgetFromItinerary(itinerary, trip);
    if (live && live.points.length > 0) return budgetFromLive(live, trip);
    return null;
  }, [itinerary, live, trip]);

  if (!cityCenter) {
    return (
      <div className="flex h-full items-center justify-center bg-surface font-mono text-sm text-muted">
        <span className="typing-dot mr-2 h-2 w-2 rounded-full bg-primary" />
        {phase === "streaming" ? t.signalAcquiring : t.noRoute}
      </div>
    );
  }

  return (
    <div className="relative h-full">
      <div className="absolute inset-0">
        <MapView
          center={cityCenter}
          itinerary={itinerary}
          selectedDay={selectedDay}
          currency={trip.currency}
          livePoints={live?.points}
          mapRef={mapRef}
          fitEnabledRef={fitEnabledRef}
          playing={playing}
          onPlayEnd={() => setPlaying(false)}
        />
      </div>

      {/* HUD qatı — Leaflet pane-lərinin (max 700) üstündə */}
      <div className="pointer-events-none absolute inset-0 z-[1000]">
        {itinerary && (
          <div className="pointer-events-auto absolute left-3 top-3">
            <DayFilterHud days={itinerary.days} selectedDay={selectedDay} onSelectDay={onSelectDay} />
          </div>
        )}

        {alloc && (
          <div className={`pointer-events-auto absolute left-3 ${itinerary ? "top-16" : "top-3"}`}>
            <BudgetGauge alloc={alloc} currency={trip.currency} />
          </div>
        )}

        {stops.length > 1 && phase !== "streaming" && (
          <div className="pointer-events-auto absolute bottom-3 left-3">
            <button
              onClick={() => setPlaying((p) => !p)}
              aria-pressed={playing}
              className="hud-panel flex items-center gap-2 px-3 py-2 font-mono text-[11px] uppercase tracking-wider text-primary-deep transition-colors hover:bg-surface active:translate-y-px"
            >
              <span aria-hidden>{playing ? "■" : "▶"}</span>
              {playing ? t.stopRoute : t.playRoute}
            </button>
          </div>
        )}

        {stops.length > 1 && (
          <div className="pointer-events-auto absolute inset-x-3 bottom-3 sm:inset-x-auto sm:left-1/2 sm:w-[min(560px,80%)] sm:-translate-x-1/2">
            <TimelineScrubber
              stops={stops}
              tracking={phase === "streaming"}
              onEngage={() => {
                fitEnabledRef.current = false;
              }}
              onScrub={(lat, lon) => mapRef.current?.setView([lat, lon], 14.5, { animate: false })}
              onSettle={(s) => mapRef.current?.flyTo([s.lat, s.lon], 15, { duration: 0.8 })}
            />
          </div>
        )}

        {itinerary && (
          <ItineraryDrawer
            open={drawerOpen}
            onToggle={setDrawerOpen}
            itinerary={itinerary}
            currency={trip.currency}
            selectedDay={selectedDay}
            onSelectDay={onSelectDay}
            tripId={trip.id}
            editable={phase === "done" && !readOnly}
            onChange={onItineraryChange}
            onError={onError}
          />
        )}
      </div>
    </div>
  );
}
