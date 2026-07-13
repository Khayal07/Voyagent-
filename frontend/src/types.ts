export interface TripInput {
  city: string;
  start_date: string;
  end_date: string;
  budget: number;
  currency: string;
  travelers: number;
  interests: string[];
  language: string;
}

export interface Trip extends TripInput {
  id: string;
  status: string;
  created_at?: string;
}

export interface AuthResponse {
  token: string;
  email: string;
}

export interface TripDetail extends Trip {
  messages: AgentMsg[];
  itinerary: Itinerary | null;
}

export interface AgentMsg {
  id: number;
  agent: "interest" | "budget" | "logistics" | "planner" | "system";
  round: number;
  role: "proposal" | "objection" | "revision" | "approval" | "final" | "info";
  content: string;
  payload?: Record<string, unknown> | null;
}

export interface ItineraryItem {
  name: string;
  category: string;
  est_cost: number;
  duration_min: number;
  lat?: number | null;
  lon?: number | null;
  start_time?: string;
}

export interface ItineraryDay {
  day: number;
  date: string;
  items: ItineraryItem[];
}

export interface Itinerary {
  days: ItineraryDay[];
  total_cost: number;
}
