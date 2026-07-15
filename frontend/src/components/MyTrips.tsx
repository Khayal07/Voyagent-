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
    return <div className="py-10 text-center text-sm text-muted">...</div>;
  }
  if (trips.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-line py-10 text-center text-sm text-muted">
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
            className="flex w-full flex-wrap items-baseline gap-x-4 gap-y-1 rounded-xl border border-line bg-bg px-4 py-3 text-left transition-all hover:-translate-y-0.5 hover:border-muted hover:shadow-panel active:translate-y-0"
          >
            <span className="font-display text-xl font-semibold">{trip.city}</span>
            <span className="font-mono text-xs text-muted">
              {trip.start_date} → {trip.end_date}
            </span>
            <span className="font-mono text-xs text-muted">
              {trip.budget} {trip.currency} · {trip.travelers} {t.people}
            </span>
            <span
              className={`ml-auto inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider ${
                trip.status === "done" ? "text-ok" : "text-primary-deep"
              }`}
            >
              <span
                aria-hidden
                className={`h-1.5 w-1.5 rounded-full ${trip.status === "done" ? "bg-ok" : "bg-primary-bright"}`}
              />
              {trip.status}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
