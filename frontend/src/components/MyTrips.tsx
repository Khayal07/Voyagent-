import { useEffect, useState } from "react";
import { listTrips } from "../api";
import { useT } from "../i18n";
import type { Trip } from "../types";

interface Props {
  onOpen: (tripId: string) => void;
  onError: (detail: string) => void;
}

export default function MyTrips({ onOpen, onError }: Props) {
  const t = useT();
  const [trips, setTrips] = useState<Trip[] | null>(null);

  useEffect(() => {
    listTrips()
      .then(setTrips)
      .catch((e) => onError(e instanceof Error ? e.message : t.requestFailed));
  }, []);

  if (trips === null) {
    return <div className="py-10 text-center text-sm text-ink-soft">...</div>;
  }
  if (trips.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line py-10 text-center text-sm text-ink-soft">
        {t.noTrips}
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {trips.map((trip) => (
        <li key={trip.id}>
          <button
            onClick={() => onOpen(trip.id)}
            className="flex w-full flex-wrap items-baseline gap-x-4 gap-y-1 rounded-lg border border-line bg-panel px-4 py-3 text-left transition-colors hover:border-cyan/50"
          >
            <span className="font-display text-lg font-extrabold">{trip.city}</span>
            <span className="font-mono text-xs text-ink-soft">
              {trip.start_date} → {trip.end_date}
            </span>
            <span className="font-mono text-xs text-ink-soft">
              {trip.budget} {trip.currency} · {trip.travelers} {t.people}
            </span>
            <span
              className={`ml-auto font-mono text-[11px] uppercase tracking-wider ${
                trip.status === "done" ? "text-ok" : "text-cyan"
              }`}
            >
              {trip.status}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
