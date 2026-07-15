import { animate, motion, useMotionValue, useReducedMotion } from "motion/react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useT } from "../../i18n";
import { DAY_COLORS } from "../MapView";

export interface ScrubStop {
  name: string;
  lat: number;
  lon: number;
  day: number;
}

const HANDLE = 18; // px

interface Props {
  stops: ScrubStop[];
  onScrub: (lat: number, lon: number) => void; // drag boyunca (animasiyasız setView)
  onSettle: (stop: ScrubStop) => void; // buraxılanda flyTo
  onEngage: () => void; // ilk drag — FitBounds söndürülür
  tracking: boolean; // streaming: yeni düşən nöqtəni avtomatik izlə
}

// Video-montaj üslublu xronoloji scrubber: sürüşdürmə kameranı
// marşrut nöqtələri arasında lerp ilə uçurur.
export default function TimelineScrubber({ stops, onScrub, onSettle, onEngage, tracking }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const trackRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const [activeIdx, setActiveIdx] = useState(0);
  const engagedRef = useRef(false);
  const rafRef = useRef(0);
  const queuedRef = useRef<{ lat: number; lon: number } | null>(null);

  const usable = () => Math.max(1, (trackRef.current?.clientWidth ?? 1) - HANDLE);
  const idxToPx = (i: number) => (stops.length < 2 ? 0 : (i / (stops.length - 1)) * usable());

  const queueScrub = (lat: number, lon: number) => {
    queuedRef.current = { lat, lon };
    if (!rafRef.current) {
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = 0;
        const q = queuedRef.current;
        if (q) onScrub(q.lat, q.lon);
        queuedRef.current = null;
      });
    }
  };
  useEffect(() => () => cancelAnimationFrame(rafRef.current), []);

  const handleDrag = () => {
    if (stops.length < 2) return;
    const p = Math.min(1, Math.max(0, x.get() / usable()));
    const f = p * (stops.length - 1);
    const i = Math.floor(f);
    const frac = f - i;
    const a = stops[i];
    const b = stops[Math.min(i + 1, stops.length - 1)];
    queueScrub(a.lat + (b.lat - a.lat) * frac, a.lon + (b.lon - a.lon) * frac);
    const nearest = Math.round(f);
    if (nearest !== activeIdx) setActiveIdx(nearest);
  };

  const handleDragEnd = () => {
    if (stops.length < 2) return;
    const p = Math.min(1, Math.max(0, x.get() / usable()));
    const nearest = Math.round(p * (stops.length - 1));
    setActiveIdx(nearest);
    if (reduced) {
      x.set(idxToPx(nearest));
    } else {
      animate(x, idxToPx(nearest), { type: "spring", stiffness: 300, damping: 30 });
    }
    onSettle(stops[nearest]);
  };

  // Streaming "tracking" rejimi: istifadəçi tutmayıbsa yeni nöqtəyə sürüş
  useEffect(() => {
    if (!tracking || engagedRef.current || stops.length < 2) return;
    const lastIdx = stops.length - 1;
    setActiveIdx(lastIdx);
    if (reduced) x.set(idxToPx(lastIdx));
    else animate(x, idxToPx(lastIdx), { type: "spring", stiffness: 120, damping: 22 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stops.length, tracking]);

  // selectedDay/stops dəyişəndə başa qaytar. rAF: framer drag-constraint ölçməsi
  // handle-i mərkəzləşdirdiyi üçün mövqeni layout keçidindən SONRA təyin edirik.
  useLayoutEffect(() => {
    if (tracking) return;
    setActiveIdx(0);
    engagedRef.current = false;
    const id = requestAnimationFrame(() => x.set(0));
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stops]);

  if (stops.length < 2) return null;
  const current = stops[Math.min(activeIdx, stops.length - 1)];

  return (
    <div className="hud-panel px-4 py-2.5">
      <div className="mb-1.5 flex items-baseline justify-between gap-3 font-mono text-[9px] tracking-[0.18em] text-muted">
        <span>{t.timeline}</span>
        <span className="truncate normal-case tracking-normal text-[10px] text-primary-deep">
          {activeIdx + 1}/{stops.length} · {current.name}
        </span>
      </div>
      <div ref={trackRef} className="relative h-5 touch-none select-none">
        {/* Track xətti */}
        <div className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-line" />
        {/* Stop nişanları (gün rəngləri) */}
        {stops.map((s, i) => (
          <span
            key={`${s.day}-${s.name}`}
            className="absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full"
            style={{
              left: stops.length < 2 ? 0 : `calc(${(i / (stops.length - 1)) * 100}% + ${HANDLE / 2 - (i / (stops.length - 1)) * HANDLE}px)`,
              background: DAY_COLORS[(s.day - 1) % DAY_COLORS.length],
              opacity: i === activeIdx ? 1 : 0.4,
            }}
          />
        ))}
        {/* Sürüşən başlıq */}
        <motion.div
          drag="x"
          dragConstraints={trackRef}
          dragElastic={0}
          dragMomentum={false}
          onDragStart={() => {
            engagedRef.current = true;
            onEngage();
          }}
          onDrag={handleDrag}
          onDragEnd={handleDragEnd}
          style={{ x, width: HANDLE, height: HANDLE }}
          whileDrag={{ scale: 1.15 }}
          className="absolute top-1/2 -translate-y-1/2 cursor-grab rounded-full border-2 border-primary bg-ink shadow-md active:cursor-grabbing"
          role="slider"
          aria-label={t.scrubHint}
          aria-valuemin={1}
          aria-valuemax={stops.length}
          aria-valuenow={activeIdx + 1}
          aria-valuetext={current.name}
        />
      </div>
    </div>
  );
}
