import { useT } from "../../i18n";
import { DAY_COLORS } from "../MapView";
import type { ItineraryDay } from "../../types";

interface Props {
  days: ItineraryDay[];
  selectedDay: number;
  onSelectDay: (day: number) => void;
}

// Xəritə üstündə gün filtri çipləri
export default function DayFilterHud({ days, selectedDay, onSelectDay }: Props) {
  const t = useT();
  if (days.length === 0) return null;

  return (
    <div className="hud-glass flex flex-wrap gap-1 px-2 py-1.5" role="tablist">
      <button
        role="tab"
        aria-selected={selectedDay === 0}
        onClick={() => onSelectDay(0)}
        className={`rounded px-2.5 py-1 font-mono text-[11px] transition-colors ${
          selectedDay === 0 ? "bg-cyan text-void" : "text-ink-soft hover:text-ink"
        }`}
      >
        {t.all}
      </button>
      {days.map((d) => {
        const color = DAY_COLORS[(d.day - 1) % DAY_COLORS.length];
        const active = selectedDay === d.day;
        return (
          <button
            key={d.day}
            role="tab"
            aria-selected={active}
            onClick={() => onSelectDay(d.day)}
            className={`rounded px-2.5 py-1 font-mono text-[11px] transition-colors ${
              active ? "text-void" : "text-ink-soft hover:text-ink"
            }`}
            style={active ? { background: color } : undefined}
          >
            {t.day} {d.day}
          </button>
        );
      })}
    </div>
  );
}
