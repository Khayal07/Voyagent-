import { useEffect, useMemo, useState } from "react";
import type { AgentMsg } from "../types";

export type AgentName = "interest" | "budget" | "logistics" | "planner";
export type AgentStatus = "idle" | "thinking" | "objecting" | "approved";

export const AGENT_NAMES: AgentName[] = ["interest", "budget", "logistics", "planner"];

export interface Conflict {
  agent: AgentName;
  round: number;
  msgId: number;
  content: string;
  resolved: boolean;
}

// Son canlı mesajın sahibi bu müddət qədər "düşünür" görünür
const THINKING_DECAY_MS = 6000;

// Mesaj axınından hər agentin vəziyyətini çıxarır (heç bir əlavə server datası yoxdur).
// objection → objecting; sonrakı revision onu bağlayır; approval/final → approved.
export function useAgentStatuses(messages: AgentMsg[], status: string) {
  const [tick, setTick] = useState(0);
  const last = messages.length > 0 ? messages[messages.length - 1] : undefined;

  // "thinking" vəziyyətinin 6 saniyəlik sönməsi üçün taymer
  useEffect(() => {
    if (!last?.live || !last.receivedAt) return;
    const remain = last.receivedAt + THINKING_DECAY_MS - Date.now();
    if (remain <= 0) return;
    const id = setTimeout(() => setTick((n) => n + 1), remain + 50);
    return () => clearTimeout(id);
  }, [last]);

  return useMemo(() => {
    void tick;
    const statuses: Record<AgentName, AgentStatus> = {
      interest: "idle",
      budget: "idle",
      logistics: "idle",
      planner: "idle",
    };
    const conflicts: Conflict[] = [];

    for (const m of messages) {
      if (m.agent === "system") continue;
      const agent = m.agent as AgentName;
      if (m.role === "objection") {
        conflicts.push({ agent, round: m.round, msgId: m.id, content: m.content, resolved: false });
        statuses[agent] = "objecting";
      } else if (m.role === "revision") {
        for (const c of conflicts) {
          if (!c.resolved && c.msgId < m.id) {
            c.resolved = true;
            statuses[c.agent] = "idle";
          }
        }
      } else if (m.role === "approval" || m.role === "final") {
        statuses[agent] = "approved";
        for (const c of conflicts) {
          if (!c.resolved && c.agent === agent) c.resolved = true;
        }
      }
    }

    if (status === "done") {
      for (const a of AGENT_NAMES) statuses[a] = "approved";
      // Yekun plan çıxıbsa açıq qalan etirazlar da konsensusla bağlanmış sayılır
      for (const c of conflicts) c.resolved = true;
    } else if (status === "pending" || status === "planning") {
      // Radar süpürməsi son danışan agentdə qalır (yalnız canlı mesaj üçün)
      if (
        last &&
        last.agent !== "system" &&
        last.live &&
        last.receivedAt &&
        Date.now() - last.receivedAt < THINKING_DECAY_MS &&
        statuses[last.agent as AgentName] !== "objecting"
      ) {
        statuses[last.agent as AgentName] = "thinking";
      }
    }

    return { statuses, conflicts };
  }, [messages, status, last, tick]);
}
