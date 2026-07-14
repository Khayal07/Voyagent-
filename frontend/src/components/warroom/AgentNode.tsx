import { motion, useReducedMotion } from "motion/react";
import { useT } from "../../i18n";
import type { AgentName, AgentStatus } from "../../hooks/useAgentStatuses";

const AGENT_HEX: Record<AgentName, string> = {
  interest: "#a78bfa",
  budget: "#4ade80",
  logistics: "#f5b841",
  planner: "#5eb3e4",
};

interface Props {
  agent: AgentName;
  status: AgentStatus;
}

export default function AgentNode({ agent, status }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const hex = AGENT_HEX[agent];

  const ringStyle =
    status === "thinking"
      ? { borderColor: hex, boxShadow: `0 0 10px ${hex}59, 0 0 24px ${hex}26` }
      : status === "approved"
        ? { borderColor: "var(--color-ok)", boxShadow: "0 0 8px rgb(63 224 160 / 0.3)" }
        : status === "objecting"
          ? undefined // alert-flash CSS-i idarə edir
          : { borderColor: "var(--color-line)" };

  return (
    <div className="flex min-w-0 flex-col items-center gap-1.5">
      <motion.div
        className={`relative flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-2 bg-panel-2 ${
          status === "objecting" ? "alert-flash" : ""
        } ${status === "idle" ? "opacity-55" : ""}`}
        style={ringStyle}
        animate={
          reduced
            ? undefined
            : status === "thinking"
              ? { scale: [1, 1.06, 1] }
              : status === "objecting"
                ? { x: [0, -3, 3, -2, 2, 0], scale: 1 }
                : { scale: 1 }
        }
        transition={
          status === "thinking"
            ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" }
            : status === "objecting"
              ? { duration: 0.4 }
              : { type: "spring", stiffness: 400, damping: 26 }
        }
      >
        {status === "thinking" && !reduced && (
          <span className="radar-sweep pointer-events-none absolute inset-0 rounded-full" />
        )}
        <span
          className="relative font-mono text-[11px] font-semibold uppercase"
          style={{ color: status === "idle" ? "var(--color-ink-soft)" : hex }}
        >
          {t.agents[agent].slice(0, 2)}
        </span>
        {status === "approved" && (
          <motion.span
            initial={reduced ? false : { scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 22 }}
            className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-ok text-[9px] font-bold text-void"
          >
            ✓
          </motion.span>
        )}
      </motion.div>
      <span className="max-w-16 truncate font-mono text-[9px] uppercase tracking-wider text-ink-soft">
        {t.agents[agent]}
      </span>
      <span
        className="font-mono text-[9px] lowercase"
        style={{
          color:
            status === "objecting"
              ? "var(--color-alert)"
              : status === "approved"
                ? "var(--color-ok)"
                : status === "thinking"
                  ? hex
                  : "var(--color-ink-soft)",
        }}
      >
        {t.agentStatus[status]}
      </span>
    </div>
  );
}
