import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { clearAuth, createTrip, getEmail, getSharedTrip, getTrip, openTripStream, SessionExpiredError } from "./api";
import AuthForm from "./components/AuthForm";
import MissionControl from "./components/MissionControl";
import MyTrips from "./components/MyTrips";
import PrintableItinerary from "./components/PrintableItinerary";
import TripForm from "./components/TripForm";
import { LangContext, getInitialLang, translations, type Lang } from "./i18n";
import { derivePhase, initialStreamState, streamReducer } from "./streamState";
import type { Trip, TripInput } from "./types";

export default function App() {
  const [lang, setLang] = useState<Lang>(getInitialLang);
  const [userEmail, setUserEmail] = useState<string | null>(getEmail);
  const [view, setView] = useState<"planner" | "myTrips">("planner");
  const [trip, setTrip] = useState<Trip | null>(null);
  const [stream, dispatch] = useReducer(streamReducer, initialStreamState);
  const [error, setError] = useState("");
  const [selectedDay, setSelectedDay] = useState(0);
  const closeRef = useRef<(() => void) | null>(null);
  // Oxu-yalnız paylaşma rejimi: /?share=TOKEN — auth tələb olunmur
  const [shareToken] = useState(() => new URLSearchParams(window.location.search).get("share"));

  useEffect(() => () => closeRef.current?.(), []);

  useEffect(() => {
    if (!shareToken) return;
    getSharedTrip(shareToken)
      .then((detail) => {
        setTrip(detail);
        dispatch({
          type: "replay",
          messages: detail.messages,
          status: detail.status,
          itinerary: detail.itinerary,
        });
      })
      .catch(() => setError(translations[getInitialLang()].shareInvalid));
  }, [shareToken]);

  useEffect(() => {
    localStorage.setItem("voyagent-lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const t = translations[lang];
  const { messages, status, itinerary } = stream;
  const phase = derivePhase(trip, status);

  // Şəhərin mərkəzi ilk system mesajının payload-ından gəlir
  const cityCenter = useMemo<[number, number] | null>(() => {
    const m = messages.find((x) => x.agent === "system" && x.payload && "lat" in x.payload);
    return m ? [m.payload!.lat as number, m.payload!.lon as number] : null;
  }, [messages]);

  const handleApiError = (e: unknown) => {
    if (e instanceof SessionExpiredError) {
      setUserEmail(null);
      setError(t.sessionExpired);
    } else {
      setError(e instanceof Error ? e.message : t.requestFailed);
    }
  };

  const attachStream = (tripId: string) => {
    closeRef.current?.();
    closeRef.current = openTripStream(tripId, {
      onMessage: (m) => dispatch({ type: "live_message", msg: m }),
      onStatus: (s) => dispatch({ type: "status", status: s }),
      onItinerary: (it) => dispatch({ type: "itinerary", itinerary: it }),
      onDone: () => {},
      onError: (detail) => setError(detail),
    });
  };

  const start = async (input: Omit<TripInput, "language">) => {
    setError("");
    dispatch({ type: "reset" });
    setSelectedDay(0);
    try {
      const t2 = await createTrip({ ...input, language: lang });
      setTrip(t2);
      dispatch({ type: "status", status: "planning" });
      attachStream(t2.id);
    } catch (e) {
      handleApiError(e);
    }
  };

  // "Səyahətlərim"dən köhnə trip-i açır; hələ bitməyibsə canlı stream-ə qoşulur
  const openPastTrip = async (tripId: string) => {
    setError("");
    try {
      const detail = await getTrip(tripId);
      setTrip(detail);
      dispatch({
        type: "replay",
        messages: detail.messages,
        status: detail.status,
        itinerary: detail.itinerary,
      });
      setSelectedDay(0);
      setView("planner");
      if (detail.status === "pending" || detail.status === "planning") {
        attachStream(tripId);
      }
    } catch (e) {
      handleApiError(e);
    }
  };

  const reset = () => {
    closeRef.current?.();
    setTrip(null);
    dispatch({ type: "reset" });
    setError("");
  };

  const logout = () => {
    reset();
    clearAuth();
    setUserEmail(null);
    setView("planner");
  };

  const langSwitcher = (
    <div
      className="flex overflow-hidden rounded-lg border border-line font-mono text-xs"
      role="group"
      aria-label="Language"
    >
      {(["en", "az"] as Lang[]).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`px-2.5 py-1.5 transition-colors ${
            lang === l ? "bg-ink text-white" : "text-muted hover:text-ink"
          }`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      {trip && itinerary && <PrintableItinerary trip={trip} itinerary={itinerary} />}
      <div className="app-screen mx-auto flex h-screen max-w-[1700px] flex-col px-4 py-5">
        <header className="rule-double mb-6 flex items-end justify-between pb-4">
          <div>
            <h1 className="font-display text-3xl font-semibold tracking-tight">
              Voyagent<span className="text-primary">.</span>
            </h1>
            <p className="font-mono text-[11px] tracking-[0.25em] text-muted">{t.tagline}</p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
            {langSwitcher}
            {shareToken && (
              <span className="rounded-md bg-surface-2 px-2 py-1 font-mono text-[10px] tracking-widest text-muted">
                {t.viewOnly}
              </span>
            )}
            {userEmail && !shareToken && (
              <>
                <button
                  onClick={() => {
                    setError("");
                    if (view === "myTrips") {
                      setView("planner");
                    } else {
                      reset();
                      setView("myTrips");
                    }
                  }}
                  className="rounded-lg border border-line px-3 py-1.5 text-sm text-ink transition-all hover:border-muted hover:bg-surface active:translate-y-px"
                >
                  {view === "myTrips" ? t.backToPlanner : t.myTrips}
                </button>
                {trip && view === "planner" && (
                  <button
                    onClick={reset}
                    className="rounded-lg border border-line px-3 py-1.5 text-sm text-ink transition-all hover:border-muted hover:bg-surface active:translate-y-px"
                  >
                    {t.newTrip}
                  </button>
                )}
                <div className="hidden items-baseline gap-2 sm:flex">
                  <span className="font-mono text-xs text-muted">{userEmail}</span>
                  <button
                    onClick={logout}
                    className="text-sm text-muted underline-offset-2 transition-colors hover:text-ink hover:underline"
                  >
                    {t.logout}
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        {error && (
          <div className="mb-4 rounded-lg border border-alert/40 bg-alert/5 px-4 py-3 text-sm text-alert">
            {error}
          </div>
        )}

        {shareToken ? (
          trip ? (
            <div className="flex min-h-0 flex-1 flex-col">
              <MissionControl
                trip={trip}
                phase={phase}
                status={status}
                messages={messages}
                itinerary={itinerary}
                cityCenter={cityCenter}
                selectedDay={selectedDay}
                onSelectDay={setSelectedDay}
                onItineraryChange={(it) => dispatch({ type: "itinerary", itinerary: it })}
                onError={setError}
                readOnly
              />
            </div>
          ) : !error ? (
            <p className="py-10 text-center font-mono text-sm text-muted">{t.loadingTrip}</p>
          ) : null
        ) : !userEmail ? (
          <AuthForm
            onAuthed={(email) => {
              setError("");
              setUserEmail(email);
            }}
          />
        ) : view === "myTrips" ? (
          <div className="min-h-0 flex-1 overflow-y-auto">
            <MyTrips onOpen={openPastTrip} onError={handleApiError} />
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {!trip ? (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, filter: "blur(4px)" }}
                transition={{ duration: 0.3 }}
                className="mx-auto w-full max-w-xl overflow-y-auto py-6"
              >
                <TripForm onSubmit={start} busy={false} />
              </motion.div>
            ) : (
              <motion.div
                key="mission"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.35 }}
                className="flex min-h-0 flex-1 flex-col"
              >
                <MissionControl
                  trip={trip}
                  phase={phase}
                  status={status}
                  messages={messages}
                  itinerary={itinerary}
                  cityCenter={cityCenter}
                  selectedDay={selectedDay}
                  onSelectDay={setSelectedDay}
                  onItineraryChange={(it) => dispatch({ type: "itinerary", itinerary: it })}
                  onError={setError}
                />
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>
    </LangContext.Provider>
  );
}
