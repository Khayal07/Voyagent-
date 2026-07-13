import { useEffect, useRef } from "react";
import { useT } from "../i18n";
import type { AgentMsg } from "../types";
import AgentMessage from "./AgentMessage";

interface Props {
  messages: AgentMsg[];
  planning: boolean;
}

export default function AgentChat({ messages, planning }: Props) {
  const t = useT();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, planning]);

  return (
    <aside className="flex h-full min-h-0 flex-col rounded-lg border border-line bg-mist/60">
      <header className="flex items-center justify-between border-b border-line px-4 py-3">
        <span className="font-mono text-xs font-medium tracking-[0.2em] text-ink-soft">
          {t.liveChat}
        </span>
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-ink-soft">
          <span
            className={`h-2 w-2 rounded-full ${planning ? "bg-route typing-dot" : "bg-agent-budget"}`}
          />
          {planning ? t.statusActive : t.statusIdle}
        </span>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !planning && (
          <p className="py-8 text-center text-sm text-ink-soft">{t.chatEmpty}</p>
        )}
        <div className="route-thread ml-1.5">
          {messages.map((m) => (
            <AgentMessage key={m.id} msg={m} />
          ))}
          {planning && (
            <div className="flex items-center gap-1.5 pl-6 pt-1">
              <span className="typing-dot h-1.5 w-1.5 rounded-full bg-ink-soft" />
              <span className="typing-dot h-1.5 w-1.5 rounded-full bg-ink-soft" />
              <span className="typing-dot h-1.5 w-1.5 rounded-full bg-ink-soft" />
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </div>
    </aside>
  );
}
