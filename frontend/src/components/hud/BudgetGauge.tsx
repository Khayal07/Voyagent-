import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { useEffect } from "react";
import { useT } from "../../i18n";
import type { BudgetAllocation } from "../../lib/budget";

const ARC = 0.75; // 270° qövs

interface Props {
  alloc: BudgetAllocation;
  currency: string;
}

// Radial büdcə bölgüsü: qövs seqmentləri büdcənin fraksiyalarıdır.
// Boş qalan hissə = ehtiyat; aşılıbsa halqa qırmızı yanır.
export default function BudgetGauge({ alloc, currency }: Props) {
  const t = useT();
  const reduced = useReducedMotion();
  const { budget, over } = alloc;

  // Mərkəzdəki rəqəm asta spring ilə "sayır"
  const spentSpring = useSpring(alloc.spent, { stiffness: 60, damping: 16 });
  useEffect(() => {
    if (reduced) spentSpring.jump(alloc.spent);
    else spentSpring.set(alloc.spent);
  }, [alloc.spent, reduced, spentSpring]);
  const spentText = useTransform(spentSpring, (v) => String(Math.round(v)));

  const segments = [
    { key: "lodging", value: alloc.lodging, color: "#00f2fe", label: t.gauge.lodging },
    { key: "food", value: alloc.food, color: "#d4af37", label: t.gauge.food },
    { key: "fun", value: alloc.fun, color: "#4ade80", label: t.gauge.fun },
  ];

  // Fraksiyalar (cəmi 1-i keçməsin — aşımda proporsional sıxılır)
  const spentFrac = budget > 0 ? Math.min(1, alloc.spent / budget) : 1;
  const scale = alloc.spent > 0 ? spentFrac / (alloc.spent / (budget || 1)) : 1;
  let cursor = 0;
  const arcs = segments.map((s) => {
    const frac = budget > 0 ? (s.value / budget) * scale : 0;
    const arc = { ...s, start: cursor, len: frac };
    cursor += frac;
    return arc;
  });

  const spring = reduced
    ? { duration: 0.2 }
    : { type: "spring" as const, stiffness: 60, damping: 16 };

  return (
    <div className="hud-glass w-44 px-3 py-2.5">
      <div className="mb-1 font-mono text-[9px] font-medium tracking-[0.18em] text-ink-soft">
        {t.budgetGauge}
      </div>
      <div className="flex items-center gap-2.5">
        <motion.svg
          viewBox="0 0 100 100"
          className="h-20 w-20 shrink-0"
          animate={over && !reduced ? { scale: [1, 1.04, 1] } : { scale: 1 }}
          transition={over ? { duration: 1.2, repeat: Infinity } : undefined}
        >
          <g transform="rotate(135 50 50)">
            {/* Track (boş hissə = ehtiyat) */}
            <circle
              cx="50" cy="50" r="40" fill="none"
              stroke={over ? "rgb(255 51 102 / 0.4)" : "#1e2a44"}
              strokeWidth="9" strokeLinecap="round"
              pathLength={1}
              strokeDasharray={`${ARC} ${1 - ARC}`}
            />
            {arcs.map(
              (a) =>
                a.len > 0.001 && (
                  <motion.circle
                    key={a.key}
                    cx="50" cy="50" r="40" fill="none"
                    stroke={a.color} strokeWidth="9"
                    pathLength={1}
                    strokeLinecap="butt"
                    initial={false}
                    animate={{
                      strokeDasharray: `${a.len * ARC} ${1 - a.len * ARC}`,
                      strokeDashoffset: -(a.start * ARC),
                    }}
                    transition={spring}
                  />
                ),
            )}
          </g>
          <motion.text
            x="50" y="47" textAnchor="middle"
            style={{ font: "700 15px 'IBM Plex Mono', monospace" }}
            fill={over ? "#ff3366" : "#e6edf7"}
          >
            {spentText}
          </motion.text>
          <text
            x="50" y="61" textAnchor="middle"
            style={{ font: "400 8.5px 'IBM Plex Mono', monospace" }}
            fill="#8b99b4"
          >
            / {budget} {currency}
          </text>
        </motion.svg>

        <ul className="min-w-0 flex-1 space-y-1 font-mono text-[9px] leading-tight">
          {segments.map((s) => (
            <li key={s.key} className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: s.color }} />
              <span className="truncate text-ink-soft">{s.label}</span>
              <span className="ml-auto text-ink">{Math.round(s.value)}</span>
            </li>
          ))}
          <li className="flex items-center gap-1.5">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: over ? "#ff3366" : "#1e2a44" }}
            />
            <span className={`truncate ${over ? "text-alert" : "text-ink-soft"}`}>
              {over ? t.overBudget : t.gauge.reserve}
            </span>
            <span className={`ml-auto ${over ? "text-alert" : "text-ink"}`}>
              {Math.round(alloc.reserve)}
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
