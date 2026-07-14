import { useMemo } from "react";
import type { AgentMsg, Itinerary } from "../types";

export interface LivePoint {
  name: string;
  lat: number;
  lon: number;
  day: number;
  category: string;
  est_cost: number;
}

export interface LiveProposal {
  points: LivePoint[];
  hotelNightly: number | null;
}

interface PayloadItem {
  name?: unknown;
  category?: unknown;
  est_cost?: unknown;
  lat?: unknown;
  lon?: unknown;
  llm_lat?: unknown;
  llm_lon?: unknown;
}

interface PayloadDay {
  day?: unknown;
  items?: PayloadItem[];
}

// Yekun itinerary-dən ƏVVƏL son interest/planner payload-undan koordinatları çıxarır —
// markerlər danışıq gedərkən xəritəyə düşür. Itinerary gələn kimi null (yekun data qalib).
export function useLivePoints(messages: AgentMsg[], itinerary: Itinerary | null): LiveProposal | null {
  return useMemo(() => {
    if (itinerary) return null;
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if ((m.agent !== "interest" && m.agent !== "planner") || !m.payload) continue;
      const days = m.payload.days;
      if (!Array.isArray(days)) continue;

      const points: LivePoint[] = [];
      for (const d of days as PayloadDay[]) {
        if (!Array.isArray(d.items)) continue;
        for (const it of d.items) {
          // Geokod hələ işləməyibsə LLM-in təxmini koordinatına düş (llm_lat/llm_lon)
          const lat = typeof it.lat === "number" ? it.lat : typeof it.llm_lat === "number" ? it.llm_lat : null;
          const lon = typeof it.lon === "number" ? it.lon : typeof it.llm_lon === "number" ? it.llm_lon : null;
          if (lat != null && lon != null && typeof it.name === "string") {
            points.push({
              name: it.name,
              lat,
              lon,
              day: typeof d.day === "number" ? d.day : 1,
              category: typeof it.category === "string" ? it.category : "other",
              est_cost: typeof it.est_cost === "number" ? it.est_cost : 0,
            });
          }
        }
      }
      const nightly = m.payload.hotel_nightly_est;
      return { points, hotelNightly: typeof nightly === "number" ? nightly : null };
    }
    return null;
  }, [messages, itinerary]);
}
