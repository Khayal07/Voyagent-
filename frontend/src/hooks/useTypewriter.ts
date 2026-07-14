import { useEffect, useRef } from "react";

// ~saniyədə 150 simvol
const CHARS_PER_FRAME = 2.5;

// Mətni rAF loop-u ilə BİRBAŞA DOM-a yazır — typing boyunca React re-render sıfırdır.
// Ref hansısa elementə bağlanıbsa: active=true → hərf-hərf yazır, active=false → dərhal tam yazır.
export function useTypewriter(text: string, active: boolean, onDone: () => void) {
  const ref = useRef<HTMLSpanElement>(null);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!active) {
      el.textContent = text;
      return;
    }
    let n = 0;
    let raf = 0;
    let finished = false;
    const step = () => {
      n += CHARS_PER_FRAME;
      const upTo = Math.min(text.length, Math.floor(n));
      el.textContent = text.slice(0, upTo);
      if (upTo >= text.length) {
        finished = true;
        onDoneRef.current();
        return;
      }
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      // Yarımçıq kəsilsə (unmount) mətni tam yaz
      if (!finished) el.textContent = text;
    };
  }, [text, active]);

  return ref;
}
