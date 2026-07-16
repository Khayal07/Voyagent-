import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useT } from "../../i18n";
import { budgetFromItinerary } from "../../lib/budget";
import type { Itinerary, Trip } from "../../types";

interface Props {
  open: boolean;
  base: Itinerary;
  sim: Itinerary;
  removed: string[];
  trip: Trip;
  onClose: () => void;
}

function stops(it: Itinerary): number {
  return it.days.reduce((n, d) => n + d.items.length, 0);
}

// A/B yan-yana müqayisə: cari plan vs simulyasiya. Xərc/dayanacaq fərqi və
// çıxarılan yerlər göstərilir.
export default function ABCompare({ open, base, sim, removed, trip, onClose }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const cur = trip.currency;

  const col = (title: string, it: Itinerary, accent: boolean) => {
    const spent = budgetFromItinerary(it, trip).spent;
    return (
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <div className="flex items-baseline justify-between">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
            {title}
          </span>
          <span className={`font-mono text-sm font-semibold ${accent ? "text-primary-deep" : "text-ink"}`}>
            {Math.round(spent)} {cur}
          </span>
        </div>
        <div className="font-mono text-[11px] text-muted">
          {stops(it)} {t.stopsLabel}
        </div>
        <ul className="space-y-1 font-mono text-[11px] leading-tight">
          {it.days.map((d) => (
            <li key={d.day} className="flex justify-between gap-2">
              <span className="text-muted">
                {t.day} {d.day}
              </span>
              <span className="text-ink">{d.items.length}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  const spentBase = budgetFromItinerary(base, trip).spent;
  const spentSim = budgetFromItinerary(sim, trip).spent;
  const delta = spentSim - spentBase;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0.1 : 0.2 }}
          className="pointer-events-auto absolute inset-0 z-[1002] flex items-center justify-center bg-ink/20 p-4"
          onClick={onClose}
        >
          <motion.div
            initial={reduced ? { opacity: 0 } : { scale: 0.96, opacity: 0 }}
            animate={reduced ? { opacity: 1 } : { scale: 1, opacity: 1 }}
            exit={reduced ? { opacity: 0 } : { scale: 0.96, opacity: 0 }}
            transition={reduced ? { duration: 0.1 } : { type: "spring", stiffness: 280, damping: 26 }}
            onClick={(e) => e.stopPropagation()}
            className="hud-panel w-full max-w-md !rounded-xl p-4"
          >
            <div className="mb-3 flex items-center justify-between border-b border-line pb-2">
              <span className="font-mono text-[11px] tracking-[0.18em] text-muted">
                {t.compareTitle}
              </span>
              <button
                onClick={onClose}
                className="rounded-md px-2 py-1 font-mono text-[11px] text-muted transition-colors hover:text-ink"
              >
                ✕
              </button>
            </div>

            <div className="flex gap-4">
              {col(t.planCurrent, base, false)}
              <div className="w-px shrink-0 bg-line" />
              {col(t.planSimulated, sim, true)}
            </div>

            <div className="mt-3 flex items-baseline justify-between border-t border-line pt-2 font-mono text-[11px]">
              <span className="text-muted">Δ</span>
              <span className={delta < 0 ? "text-ok" : "text-ink"}>
                {delta > 0 ? "+" : ""}
                {Math.round(delta)} {cur}
              </span>
            </div>

            {removed.length > 0 && (
              <div className="mt-2">
                <div className="mb-1 font-mono text-[9px] uppercase tracking-[0.18em] text-muted">
                  {t.removedLabel}
                </div>
                <div className="flex flex-wrap gap-1">
                  {removed.map((name) => (
                    <span
                      key={name}
                      className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-muted line-through"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
