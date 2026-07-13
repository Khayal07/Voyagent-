import type { AgentMsg } from "../types";

export const AGENT_META: Record<
  AgentMsg["agent"],
  { name: string; dot: string; label: string }
> = {
  interest: { name: "Maraq", dot: "bg-agent-interest", label: "text-agent-interest" },
  budget: { name: "Büdcə", dot: "bg-agent-budget", label: "text-agent-budget" },
  logistics: { name: "Logistika", dot: "bg-agent-logistics", label: "text-agent-logistics" },
  planner: { name: "Planlayıcı", dot: "bg-agent-planner", label: "text-agent-planner" },
  system: { name: "Sistem", dot: "bg-agent-system", label: "text-agent-system" },
};

const ROLE_BADGE: Record<AgentMsg["role"], { text: string; cls: string } | null> = {
  proposal: { text: "TƏKLİF", cls: "border-ink-soft text-ink-soft" },
  objection: { text: "ETİRAZ", cls: "border-route text-route" },
  revision: { text: "YENİ TƏKLİF", cls: "border-agent-interest text-agent-interest" },
  approval: { text: "TƏSDİQ", cls: "border-agent-budget text-agent-budget" },
  final: { text: "YEKUN", cls: "border-agent-planner bg-agent-planner text-white" },
  info: null,
};

export default function AgentMessage({ msg }: { msg: AgentMsg }) {
  const meta = AGENT_META[msg.agent] ?? AGENT_META.system;
  const badge = ROLE_BADGE[msg.role];

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
      <span className={`absolute left-[-6px] top-1 h-2.5 w-2.5 rounded-full ${meta.dot}`} />
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className={`font-display text-sm font-semibold ${meta.label}`}>{meta.name}</span>
        {msg.round > 0 && msg.round < 99 && (
          <span className="font-mono text-[10px] text-ink-soft">R{msg.round}</span>
        )}
        {badge && (
          <span
            className={`rounded-sm border px-1.5 py-px font-mono text-[10px] font-medium tracking-wider ${badge.cls}`}
          >
            {badge.text}
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
