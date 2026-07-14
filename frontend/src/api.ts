import type { AgentMsg, AuthResponse, Itinerary, Trip, TripDetail, TripInput } from "./types";

const TOKEN_KEY = "voyagent-token";
const EMAIL_KEY = "voyagent-email";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getEmail(): string | null {
  return localStorage.getItem(EMAIL_KEY);
}

export function setAuth(token: string, email: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(EMAIL_KEY, email);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export class SessionExpiredError extends Error {}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init?.headers },
  });
  if (resp.status === 401) {
    clearAuth();
    throw new SessionExpiredError();
  }
  if (!resp.ok) {
    const body = await resp.json().catch(() => null);
    throw new Error(body?.detail?.[0]?.msg ?? body?.detail ?? "Request failed");
  }
  return resp.json();
}

export function register(email: string, password: string): Promise<AuthResponse> {
  return request("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function createTrip(input: TripInput): Promise<Trip> {
  return request("/api/trips", { method: "POST", body: JSON.stringify(input) });
}

export function listTrips(): Promise<Trip[]> {
  return request("/api/trips");
}

export function getTrip(tripId: string): Promise<TripDetail> {
  return request(`/api/trips/${tripId}`);
}

export function getRates(base: string): Promise<{ base: string; rates: Record<string, number> }> {
  return request(`/api/rates?base=${encodeURIComponent(base)}`);
}

export function patchItinerary(
  tripId: string,
  days: { day: number; items: string[] }[],
): Promise<Itinerary> {
  return request(`/api/trips/${tripId}/itinerary`, {
    method: "PATCH",
    body: JSON.stringify({ days }),
  });
}

export interface StreamHandlers {
  onMessage: (msg: AgentMsg) => void;
  onStatus: (status: string) => void;
  onItinerary: (itinerary: Itinerary) => void;
  onDone: () => void;
  onError: (detail: string) => void;
}

export function openTripStream(tripId: string, handlers: StreamHandlers): () => void {
  // EventSource header qoya bilmir — token query param ilə göndərilir
  const token = getToken() ?? "";
  const es = new EventSource(`/api/trips/${tripId}/stream?token=${encodeURIComponent(token)}`);

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
