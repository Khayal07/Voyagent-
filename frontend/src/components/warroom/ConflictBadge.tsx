import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";
import { useT } from "../../i18n";
import type { Conflict } from "../../hooks/useAgentStatuses";

interface Props {
  conflicts: Conflict[];
}

// Canlı konflikt kartı: etiraz gələndə qırmızı yanır; həll olunanda (revision/approval)
// eyni kart yaşıl "KONSENSUS ƏLDƏ OLUNDU"-ya morph olur və 4 saniyə sonra yığılır.
// Yalnız bu sessiyada AÇIQ görünmüş konfliktlər göstərilir — replay-dəki köhnələr yox.
export default function ConflictBadge({ conflicts }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const [view, setView] = useState<{ msgId: number; state: "open" | "resolved" } | null>(null);

  const lastOpen = [...conflicts].reverse().find((c) => !c.resolved);
  const tracked = view ? conflicts.find((c) => c.msgId === view.msgId) : undefined;

  useEffect(() => {
    if (lastOpen) setView({ msgId: lastOpen.msgId, state: "open" });
  }, [lastOpen?.msgId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (view?.state === "open" && tracked?.resolved) {
      setView({ msgId: view.msgId, state: "resolved" });
      const id = setTimeout(() => setView(null), 4000);
      return () => clearTimeout(id);
    }
  }, [view, tracked?.resolved]);

  const open = view?.state === "open";

  return (
    <AnimatePresence>
      {view && (
        <motion.div
          initial={reduced ? false : { opacity: 0, y: -6 }}
          animate={{
            opacity: 1,
            y: 0,
            backgroundColor: open ? "rgba(255, 51, 102, 0.10)" : "rgba(63, 224, 160, 0.10)",
            borderColor: open ? "rgba(255, 51, 102, 0.60)" : "rgba(63, 224, 160, 0.60)",
            boxShadow: open
              ? "0 0 12px rgb(255 51 102 / 0.5), 0 0 32px rgb(255 51 102 / 0.2)"
              : "0 0 10px rgb(63 224 160 / 0.35), 0 0 24px rgb(63 224 160 / 0.12)",
          }}
          exit={{ opacity: 0, height: 0, marginTop: -12, transition: { duration: 0.35 } }}
          transition={
            reduced ? { duration: 0.15 } : { type: "spring", stiffness: 200, damping: 24 }
          }
          className="overflow-hidden rounded-lg border px-3 py-2"
        >
          <div
            className={`flex items-center gap-2 font-mono text-[10px] font-semibold tracking-widest ${
              open ? "text-alert" : "text-ok"
            }`}
          >
            <AnimatePresence mode="popLayout" initial={false}>
              <motion.span
                key={open ? "warn" : "ok"}
                initial={reduced ? false : { scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.5, opacity: 0 }}
                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                aria-hidden
              >
                {open ? "⚠" : "✓"}
              </motion.span>
            </AnimatePresence>
            {open ? t.conflictDetected : t.consensusReached}
            {tracked && <span className="font-normal opacity-70">R{tracked.round}</span>}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
