import { useEffect, useMemo, useRef, useState } from "react";
import { createTrip, openTripStream } from "./api";
import AgentChat from "./components/AgentChat";
import ItineraryPanel from "./components/ItineraryPanel";
import MapView from "./components/MapView";
import TripForm from "./components/TripForm";
import { LangContext, getInitialLang, translations, type Lang } from "./i18n";
import type { AgentMsg, Itinerary, Trip, TripInput } from "./types";

export default function App() {
  const [lang, setLang] = useState<Lang>(getInitialLang);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [messages, setMessages] = useState<AgentMsg[]>([]);
  const [status, setStatus] = useState("idle");
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState(0);
  const closeRef = useRef<(() => void) | null>(null);

  useEffect(() => () => closeRef.current?.(), []);

  useEffect(() => {
    localStorage.setItem("voyagent-lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const t = translations[lang];
  const planning = status === "pending" || status === "planning";

  // Şəhərin mərkəzi ilk system mesajının payload-ından gəlir
  const cityCenter = useMemo<[number, number] | null>(() => {
    const m = messages.find((x) => x.agent === "system" && x.payload && "lat" in x.payload);
    return m ? [m.payload!.lat as number, m.payload!.lon as number] : null;
  }, [messages]);

  const start = async (input: Omit<TripInput, "language">) => {
    setError("");
    setMessages([]);
    setItinerary(null);
    setSelectedDay(0);
    try {
      const t2 = await createTrip({ ...input, language: lang });
      setTrip(t2);
      setStatus("planning");
      closeRef.current = openTripStream(t2.id, {
        onMessage: (m) =>
          setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m])),
        onStatus: setStatus,
        onItinerary: setItinerary,
        onDone: () => {},
        onError: (detail) => setError(detail),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : t.requestFailed);
    }
  };

  const reset = () => {
    closeRef.current?.();
    setTrip(null);
    setMessages([]);
    setItinerary(null);
    setStatus("idle");
    setError("");
  };

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6">
        <header className="mb-6 flex items-end justify-between border-b-2 border-ink pb-4">
          <div>
            <h1 className="font-display text-3xl font-extrabold tracking-tight">
              Voyagent<span className="text-route">.</span>
            </h1>
            <p className="font-mono text-[11px] tracking-[0.25em] text-ink-soft">{t.tagline}</p>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="flex overflow-hidden rounded-md border border-line font-mono text-xs"
              role="group"
              aria-label="Language"
            >
              {(["en", "az"] as Lang[]).map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  aria-pressed={lang === l}
                  className={`px-2.5 py-1.5 transition-colors ${
                    lang === l ? "bg-ink text-mist" : "text-ink-soft hover:text-ink"
                  }`}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
            {trip && (
              <button
                onClick={reset}
                className="rounded-md border border-line px-3 py-1.5 text-sm text-ink-soft hover:border-ink hover:text-ink"
              >
                {t.newTrip}
              </button>
            )}
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-md border border-route bg-route/10 px-4 py-3 text-sm text-route-deep">
            {error}
          </div>
        )}

        <main className="grid flex-1 gap-6 lg:grid-cols-[1fr_400px]">
          <section className="min-w-0">
            {!trip ? (
              <TripForm onSubmit={start} busy={false} />
            ) : (
              <div className="space-y-4">
                <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-lg border border-line bg-card px-4 py-3">
                  <span className="font-display text-xl font-extrabold">{trip.city}</span>
                  <span className="font-mono text-xs text-ink-soft">
                    {trip.start_date} → {trip.end_date}
                  </span>
                  <span className="font-mono text-xs text-ink-soft">
                    {trip.budget} {trip.currency} · {trip.travelers} {t.people}
                  </span>
                </div>

                {cityCenter ? (
                  <MapView
                    center={cityCenter}
                    itinerary={itinerary}
                    selectedDay={selectedDay}
                    currency={trip.currency}
                  />
                ) : (
                  <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-line text-sm text-ink-soft">
                    {planning ? t.planningWait : t.noRoute}
                  </div>
                )}

                {itinerary && (
                  <ItineraryPanel
                    itinerary={itinerary}
                    currency={trip.currency}
                    selectedDay={selectedDay}
                    onSelectDay={setSelectedDay}
                  />
                )}
              </div>
            )}
          </section>

          <div className="h-[75vh] lg:sticky lg:top-6">
            <AgentChat messages={messages} planning={planning} />
          </div>
        </main>
      </div>
    </LangContext.Provider>
  );
}
