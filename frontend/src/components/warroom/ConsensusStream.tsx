import { useReducedMotion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useT } from "../../i18n";
import type { AgentMsg } from "../../types";
import StreamLine, { type StreamLineMode } from "./StreamLine";

interface Props {
  messages: AgentMsg[];
  planning: boolean;
  failed: boolean;
}

// Canlı log axını. Eyni anda yalnız BİR mesaj typewriter olur (FIFO);
// typedUpTo id-watermark-ı hansı mesajların artıq tam göründüyünü izləyir.
export default function ConsensusStream({ messages, planning, failed }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const [typedUpTo, setTypedUpTo] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true);

  const pendingIds = useMemo(
    () => messages.filter((m) => m.live && m.id > typedUpTo).map((m) => m.id),
    [messages, typedUpTo],
  );

  // Reduced motion: typing yoxdur. Burst (reconnect seli): yalnız ən yenisi yazılsın.
  useEffect(() => {
    if (pendingIds.length === 0) return;
    if (reduced) {
      setTypedUpTo(pendingIds[pendingIds.length - 1]);
    } else if (pendingIds.length > 3) {
      setTypedUpTo(pendingIds[pendingIds.length - 2]);
    }
  }, [pendingIds, reduced]);

  const activeId = !reduced && pendingIds.length > 0 ? pendingIds[0] : null;

  // Autoscroll: typing boyu rAF ilə; istifadəçi yuxarı sürüşübsə toxunma
  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    stickRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (activeId == null) {
      if (stickRef.current) el.scrollTop = el.scrollHeight;
      return;
    }
    let raf = 0;
    const loop = () => {
      if (stickRef.current) el.scrollTop = el.scrollHeight;
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [activeId, messages.length]);

  const modeFor = (m: AgentMsg): StreamLineMode => {
    if (!m.live || m.id <= typedUpTo) return "static";
    if (m.id === activeId) return "typing";
    return "queued";
  };

  return (
    <div className="hud-glass flex min-h-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-line/70 px-4 py-2.5">
        <span className="font-mono text-[11px] font-medium tracking-[0.2em] text-ink-soft">
          {t.consensusStream}
        </span>
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-ink-soft">
          <span
            className={`h-2 w-2 rounded-full ${
              planning ? "typing-dot bg-cyan" : failed ? "bg-alert" : "bg-ok"
            }`}
          />
          {planning ? t.statusActive : t.statusIdle}
        </span>
      </header>

      <div ref={scrollRef} onScroll={handleScroll} className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {messages.length === 0 && !planning && (
          <p className="py-8 text-center font-mono text-xs text-ink-soft">{t.chatEmpty}</p>
        )}
        {messages.map((m) => (
          <StreamLine
            key={m.id}
            msg={m}
            mode={modeFor(m)}
            onTyped={() => setTypedUpTo((prev) => Math.max(prev, m.id))}
          />
        ))}
        {planning && activeId == null && (
          <div className="flex items-center gap-1.5 px-1 pt-2">
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-cyan" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-cyan" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-cyan" />
          </div>
        )}
      </div>
    </div>
  );
}
