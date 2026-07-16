import type { AgentMsg, Itinerary, Trip } from "./types";

// SSE axını + replay üçün mərkəzi reducer.
// `live` bayrağı kritikdir: yalnız canlı gələn mesajlar typewriter animasiyası alır,
// DB replay-i dərhal tam render olunur.

export interface StreamState {
  messages: AgentMsg[];
  status: string;
  itinerary: Itinerary | null;
}

export const initialStreamState: StreamState = {
  messages: [],
  status: "idle",
  itinerary: null,
};

export type StreamAction =
  | { type: "live_message"; msg: AgentMsg }
  | { type: "replay"; messages: AgentMsg[]; status: string; itinerary: Itinerary | null }
  | { type: "status"; status: string }
  | { type: "itinerary"; itinerary: Itinerary }
  | { type: "reset" };

export function streamReducer(state: StreamState, action: StreamAction): StreamState {
  switch (action.type) {
    case "live_message": {
      // id-dedupe: replay + canlı stream eyni mesajı iki dəfə gətirə bilər
      if (state.messages.some((m) => m.id === action.msg.id)) return state;
      return {
        ...state,
        messages: [...state.messages, { ...action.msg, live: true, receivedAt: Date.now() }],
      };
    }
    case "replay":
      return {
        messages: action.messages.map((m) => ({ ...m, live: false })),
        status: action.status,
        itinerary: action.itinerary,
      };
    case "status":
      return { ...state, status: action.status };
    case "itinerary":
      return { ...state, itinerary: action.itinerary };
    case "reset":
      return initialStreamState;
    default:
      return state;
  }
}

export type Phase = "form" | "streaming" | "done" | "failed";

export function derivePhase(trip: Trip | null, status: string): Phase {
  if (!trip) return "form";
  if (status === "done") return "done";
  if (status === "failed") return "failed";
  return "streaming";
}
