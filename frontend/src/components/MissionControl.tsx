import { useState } from "react";
import { useAgentStatuses } from "../hooks/useAgentStatuses";
import { useLivePoints } from "../hooks/useLivePoints";
import { useT } from "../i18n";
import type { Phase } from "../streamState";
import type { AgentMsg, Itinerary, Trip } from "../types";
import MapCanvas from "./MapCanvas";
import AgentNodeBar from "./warroom/AgentNodeBar";
import ConflictBadge from "./warroom/ConflictBadge";
import ConsensusStream from "./warroom/ConsensusStream";

interface Props {
  trip: Trip;
  phase: Phase;
  status: string;
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
  status,
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
  const { statuses, conflicts } = useAgentStatuses(messages, status);
  const live = useLivePoints(messages, itinerary);

  const tabBtn = (tab: "war" | "map", label: string) => (
    <button
      onClick={() => setMobileTab(tab)}
      aria-pressed={mobileTab === tab}
      className={`flex-1 rounded-lg border px-3 py-2 font-mono text-xs uppercase tracking-wider transition-colors ${
        mobileTab === tab ? "border-ink bg-ink text-white" : "border-line bg-bg text-muted"
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
          <div className="panel flex flex-wrap items-baseline gap-x-4 gap-y-1 px-4 py-3">
            <span className="font-display text-xl font-semibold">{trip.city}</span>
            <span className="font-mono text-xs text-muted">
              {trip.start_date} → {trip.end_date}
            </span>
            <span className="font-mono text-xs text-muted">
              {trip.budget} {trip.currency} · {trip.travelers} {t.people}
            </span>
          </div>
          <AgentNodeBar statuses={statuses} />
          <ConflictBadge conflicts={conflicts} />
          <ConsensusStream
            key={trip.id}
            messages={messages}
            planning={planning}
            failed={phase === "failed"}
          />
        </section>

        {/* Sağ: tam-ekran radar xəritə + HUD */}
        <section
          className={`${
            mobileTab === "map" ? "flex" : "hidden"
          } panel relative min-h-0 flex-col overflow-hidden lg:flex`}
        >
          <div className="min-h-0 flex-1">
            <MapCanvas
              trip={trip}
              phase={phase}
              itinerary={itinerary}
              live={live}
              cityCenter={cityCenter}
              selectedDay={selectedDay}
              onSelectDay={onSelectDay}
              onItineraryChange={onItineraryChange}
              onError={onError}
              visible={mobileTab === "map"}
            />
          </div>
        </section>
      </div>
    </div>
  );
}
