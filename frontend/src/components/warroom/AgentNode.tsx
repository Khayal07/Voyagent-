import { motion, useReducedMotion } from "motion/react";
import { useT } from "../../i18n";
import type { AgentName, AgentStatus } from "../../hooks/useAgentStatuses";

const AGENT_COLOR: Record<AgentName, string> = {
  interest: "oklch(0.5 0.14 300)",
  budget: "oklch(0.5 0.13 155)",
  logistics: "oklch(0.52 0.12 60)",
  planner: "oklch(0.45 0.09 250)",
};

interface Props {
  agent: AgentName;
  status: AgentStatus;
}

export default function AgentNode({ agent, status }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const color = AGENT_COLOR[agent];

  const ringStyle =
    status === "thinking"
      ? { borderColor: color }
      : status === "approved"
        ? { borderColor: "var(--color-ok)" }
        : status === "objecting"
          ? { borderColor: "var(--color-alert)" }
          : { borderColor: "var(--color-line)" };

  return (
    <div className="flex min-w-0 flex-col items-center gap-1.5">
      <motion.div
        className={`relative flex h-12 w-12 items-center justify-center rounded-full border-2 bg-surface ${
          status === "idle" ? "opacity-60" : ""
        }`}
        style={ringStyle}
        animate={
          reduced
            ? undefined
            : status === "thinking"
              ? { scale: [1, 1.05, 1] }
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
        <span
          className="relative font-mono text-[11px] font-semibold uppercase"
          style={{ color: status === "idle" ? "var(--color-muted)" : color }}
        >
          {t.agents[agent].slice(0, 2)}
        </span>
        {status === "approved" && (
          <motion.span
            initial={reduced ? false : { scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 22 }}
            className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-ok text-[9px] font-bold text-white"
          >
            ✓
          </motion.span>
        )}
      </motion.div>
      <span className="max-w-16 truncate font-mono text-[9px] uppercase tracking-wider text-muted">
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
                  ? color
                  : "var(--color-muted)",
        }}
      >
        {t.agentStatus[status]}
      </span>
    </div>
  );
}
