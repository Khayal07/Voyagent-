import type { AgentMsg, Itinerary, Trip, TripInput } from "./types";

export async function createTrip(input: TripInput): Promise<Trip> {
  const resp = await fetch("/api/trips", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    throw new Error(body?.detail?.[0]?.msg ?? body?.detail ?? "Sorğu alınmadı");
  }
  return resp.json();
}

export interface StreamHandlers {
  onMessage: (msg: AgentMsg) => void;
  onStatus: (status: string) => void;
  onItinerary: (itinerary: Itinerary) => void;
  onDone: () => void;
  onError: (detail: string) => void;
}

export function openTripStream(tripId: string, handlers: StreamHandlers): () => void {
  const es = new EventSource(`/api/trips/${tripId}/stream`);

  es.addEventListener("agent_message", (e) => handlers.onMessage(JSON.parse(e.data)));
  es.addEventListener("status", (e) => handlers.onStatus(JSON.parse(e.data).status));
  es.addEventListener("itinerary", (e) => handlers.onItinerary(JSON.parse(e.data)));
  es.addEventListener("done", () => {
    handlers.onDone();
    es.close();
  });
  es.addEventListener("error", (e) => {
    if (e instanceof MessageEvent && e.data) {
      handlers.onError(JSON.parse(e.data).detail ?? "Naməlum xəta");
      es.close();
    }
  });

  return () => es.close();
}
