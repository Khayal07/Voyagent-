import { useT } from "../i18n";
import type { AgentMsg } from "../types";

const AGENT_COLORS: Record<AgentMsg["agent"], { dot: string; label: string }> = {
  interest: { dot: "bg-agent-interest", label: "text-agent-interest" },
  budget: { dot: "bg-agent-budget", label: "text-agent-budget" },
  logistics: { dot: "bg-agent-logistics", label: "text-agent-logistics" },
  planner: { dot: "bg-agent-planner", label: "text-agent-planner" },
  system: { dot: "bg-agent-system", label: "text-agent-system" },
};

const ROLE_STYLES: Record<string, string> = {
  proposal: "border-ink-soft text-ink-soft",
  objection: "border-route text-route",
  revision: "border-agent-interest text-agent-interest",
  approval: "border-agent-budget text-agent-budget",
  final: "border-agent-planner bg-agent-planner text-white",
};

export default function AgentMessage({ msg }: { msg: AgentMsg }) {
  const t = useT();
  const colors = AGENT_COLORS[msg.agent] ?? AGENT_COLORS.system;
  const badgeText = msg.role !== "info" ? t.roles[msg.role as keyof typeof t.roles] : null;

  if (msg.agent === "system") {
    return (
      <div className="relative pl-6 pb-4">
        <span className="absolute left-[-5px] top-1.5 h-2 w-2 rounded-full border-2 border-line bg-card" />
        <p className="font-mono text-[11px] leading-relaxed text-agent-system">{msg.content}</p>
      </div>
    );
  }

  return (
    <div className="relative pl-6 pb-5">
      <span className={`absolute left-[-6px] top-1 h-2.5 w-2.5 rounded-full ${colors.dot}`} />
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className={`font-display text-sm font-semibold ${colors.label}`}>
          {t.agents[msg.agent]}
        </span>
        {msg.round > 0 && msg.round < 99 && (
          <span className="font-mono text-[10px] text-ink-soft">R{msg.round}</span>
        )}
        {badgeText && (
          <span
            className={`rounded-sm border px-1.5 py-px font-mono text-[10px] font-medium tracking-wider ${
              ROLE_STYLES[msg.role] ?? ""
            }`}
          >
            {badgeText}
          </span>
        )}
      </div>
      <p
        className={`rounded-md rounded-tl-none border border-line bg-card px-3 py-2 text-sm leading-relaxed ${
          msg.role === "objection" ? "border-l-2 border-l-route" : ""
        }`}
      >
        {msg.content}
      </p>
    </div>
  );
}
