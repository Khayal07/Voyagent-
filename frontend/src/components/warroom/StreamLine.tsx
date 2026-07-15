import { motion } from "motion/react";
import { useT } from "../../i18n";
import { useTypewriter } from "../../hooks/useTypewriter";
import type { AgentMsg } from "../../types";

const LABEL_COLOR: Record<AgentMsg["agent"], string> = {
  interest: "text-agent-interest",
  budget: "text-agent-budget",
  logistics: "text-agent-logistics",
  planner: "text-agent-planner",
  system: "text-agent-system",
};

const ROLE_STYLES: Record<string, string> = {
  proposal: "border-muted/50 text-muted",
  objection: "border-alert text-alert",
  revision: "border-agent-interest text-agent-interest",
  approval: "border-ok text-ok",
  final: "border-primary-deep bg-primary/10 text-primary-deep",
};

// static: tam mətn (replay/bitmiş) · typing: hərf-hərf yazılır · queued: növbədə, mətn hələ boş
export type StreamLineMode = "static" | "typing" | "queued";

interface Props {
  msg: AgentMsg;
  mode: StreamLineMode;
  onTyped: () => void;
}

export default function StreamLine({ msg, mode, onTyped }: Props) {
  const t = useT();
  const bodyRef = useTypewriter(msg.content, mode === "typing", onTyped);

  const entrance = msg.live
    ? {
        initial: { opacity: 0, y: 10, filter: "blur(2px)" },
        animate: { opacity: 1, y: 0, filter: "blur(0px)" },
        transition: { type: "spring" as const, stiffness: 320, damping: 30 },
      }
    : { initial: false as const };

  // typing rejimində mətni rAF yazır; queued-da boş qalır; static-də React özü yazır
  const body =
    mode === "typing" ? (
      <>
        <span ref={bodyRef} />
        <span className="stream-caret text-primary">▍</span>
      </>
    ) : (
      <span>{mode === "static" ? msg.content : ""}</span>
    );

  if (msg.agent === "system") {
    return (
      <motion.div
        {...entrance}
        className="px-1 py-1.5 font-mono text-[11px] leading-relaxed text-agent-system"
      >
        <span className="mr-1.5 select-none text-accent">::</span>
        {body}
      </motion.div>
    );
  }

  const badgeText = msg.role !== "info" ? t.roles[msg.role as keyof typeof t.roles] : null;

  return (
    <motion.div {...entrance} className="px-1 py-2">
      <div className="mb-1 flex flex-wrap items-center gap-2 font-mono text-[11px]">
        <span className={`font-semibold uppercase tracking-wider ${LABEL_COLOR[msg.agent]}`}>
          [{t.agents[msg.agent]}]
        </span>
        {msg.round > 0 && msg.round < 99 && <span className="text-muted">R{msg.round}</span>}
        {badgeText && (
          <span
            className={`rounded-sm border px-1.5 py-px text-[9px] font-medium tracking-widest ${
              ROLE_STYLES[msg.role] ?? ""
            }`}
          >
            {badgeText}
          </span>
        )}
      </div>
      <p
        className={`whitespace-pre-wrap border-l pl-3 font-mono text-xs leading-relaxed text-ink/90 ${
          msg.role === "objection" ? "border-alert/70" : "border-line"
        }`}
      >
        {body}
      </p>
    </motion.div>
  );
}
