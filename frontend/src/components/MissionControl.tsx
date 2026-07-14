import { useState } from "react";
import { useT } from "../i18n";
import type { Phase } from "../streamState";
import type { AgentMsg, Itinerary, Trip } from "../types";
import AgentChat from "./AgentChat";
import ItineraryPanel from "./ItineraryPanel";
import MapView from "./MapView";

interface Props {
  trip: Trip;
  phase: Phase;
  messages: AgentMsg[];
  itinerary: Itinerary | null;
  cityCenter: [number, number] | null;
  selectedDay: number;
  onSelectDay: (day: number) => void;
  onItineraryChange: (it: Itinerary) => void;
  onError: (detail: string) => void;
}

export default function MissionControl({
  trip,
  phase,
  messages,
  itinerary,
  cityCenter,
  selectedDay,
  onSelectDay,
  onItineraryChange,
  onError,
}: Props) {
  const t = useT();
  const [mobileTab, setMobileTab] = useState<"war" | "map">("war");
  const planning = phase === "streaming";

  const tabBtn = (tab: "war" | "map", label: string) => (
    <button
      onClick={() => setMobileTab(tab)}
      aria-pressed={mobileTab === tab}
      className={`flex-1 rounded-md px-3 py-2 font-mono text-xs uppercase tracking-wider transition-colors ${
        mobileTab === tab ? "bg-cyan text-void" : "bg-panel text-ink-soft"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Mobil tab keçidi — lg-dən aşağıda split-screen sığmır */}
      <div className="mb-3 flex gap-1.5 lg:hidden">
        {tabBtn("war", t.tabWarRoom)}
        {tabBtn("map", t.tabMap)}
      </div>

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(340px,35fr)_65fr]">
        {/* Sol: Agent War Room */}
        <section
          className={`${mobileTab === "war" ? "flex" : "hidden"} min-h-0 flex-col gap-3 lg:flex`}
        >
          <div className="hud-glass flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3">
            <span className="font-display text-xl font-extrabold">{trip.city}</span>
            <span className="font-mono text-xs text-ink-soft">
              {trip.start_date} → {trip.end_date}
            </span>
            <span className="font-mono text-xs text-ink-soft">
              {trip.budget} {trip.currency} · {trip.travelers} {t.people}
            </span>
          </div>
          <div className="min-h-0 flex-1">
            <AgentChat messages={messages} planning={planning} />
          </div>
        </section>

        {/* Sağ: xəritə kanvası (HUD overlay-lər sonrakı mərhələdə bura gəlir) */}
        <section
          className={`${
            mobileTab === "map" ? "flex" : "hidden"
          } relative min-h-0 flex-col overflow-hidden rounded-xl border border-line lg:flex`}
        >
          {cityCenter ? (
            <div className="min-h-0 flex-1">
              <MapView
                center={cityCenter}
                itinerary={itinerary}
                selectedDay={selectedDay}
                currency={trip.currency}
              />
            </div>
          ) : (
            <div className="flex flex-1 items-center justify-center bg-panel/40 font-mono text-sm text-ink-soft">
              <span className="typing-dot mr-2 h-2 w-2 rounded-full bg-cyan" />
              {planning ? t.signalAcquiring : t.noRoute}
            </div>
          )}

          {itinerary && (
            <div className="max-h-[45%] overflow-y-auto border-t border-line">
              <ItineraryPanel
                itinerary={itinerary}
                currency={trip.currency}
                selectedDay={selectedDay}
                onSelectDay={onSelectDay}
                tripId={trip.id}
                editable={phase === "done"}
                onChange={onItineraryChange}
                onError={onError}
              />
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
