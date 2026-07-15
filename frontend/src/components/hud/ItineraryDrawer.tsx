import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useT } from "../../i18n";
import type { Itinerary } from "../../types";
import ItineraryPanel from "../ItineraryPanel";

interface Props {
  open: boolean;
  onToggle: (open: boolean) => void;
  itinerary: Itinerary;
  currency: string;
  selectedDay: number;
  onSelectDay: (day: number) => void;
  tripId: string;
  editable: boolean;
  onChange: (it: Itinerary) => void;
  onError: (detail: string) => void;
}

// Xəritə üzərində sağdan sürüşən marşrut paneli
export default function ItineraryDrawer({ open, onToggle, ...panel }: Props) {
  const t = useT();
  const reduced = useReducedMotion();

  return (
    <>
      {!open && (
        <button
          onClick={() => onToggle(true)}
          className="hud-panel pointer-events-auto absolute right-3 top-3 z-[1001] px-3 py-2 font-mono text-[11px] uppercase tracking-wider text-primary-deep transition-colors hover:bg-surface"
        >
          ☰ {t.showItinerary}
        </button>
      )}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={reduced ? { opacity: 0 } : { x: "100%" }}
            animate={reduced ? { opacity: 1 } : { x: 0 }}
            exit={reduced ? { opacity: 0 } : { x: "100%" }}
            transition={
              reduced ? { duration: 0.15 } : { type: "spring", stiffness: 260, damping: 30 }
            }
            className="pointer-events-auto absolute inset-y-0 right-0 z-[1001] flex w-full flex-col sm:w-[420px]"
          >
            <div className="hud-panel m-2 flex min-h-0 flex-1 flex-col !rounded-xl">
              <div className="flex items-center justify-between border-b border-line px-4 py-2">
                <span className="font-mono text-[11px] tracking-[0.18em] text-muted">
                  {t.showItinerary.toUpperCase()}
                </span>
                <button
                  onClick={() => onToggle(false)}
                  className="rounded-md px-2 py-1 font-mono text-[11px] text-muted transition-colors hover:text-ink"
                >
                  ✕ {t.hideItinerary}
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto">
                <ItineraryPanel {...panel} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
