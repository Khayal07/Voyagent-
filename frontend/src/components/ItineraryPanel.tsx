import { useT } from "../i18n";
import type { Itinerary } from "../types";
import { useRates } from "../useRates";
import { weatherEmoji } from "../weather";
import { DAY_COLORS } from "./MapView";

interface Props {
  itinerary: Itinerary;
  currency: string;
  selectedDay: number;
  onSelectDay: (day: number) => void;
}

export default function ItineraryPanel({ itinerary, currency, selectedDay, onSelectDay }: Props) {
  const t = useT();
  const rates = useRates(currency);
  const visibleDays =
    selectedDay === 0 ? itinerary.days : itinerary.days.filter((d) => d.day === selectedDay);

  return (
    <div className="rounded-lg border border-line bg-card">
      <div className="flex flex-wrap gap-1.5 border-b border-line px-4 py-3" role="tablist">
        <button
          role="tab"
          aria-selected={selectedDay === 0}
          onClick={() => onSelectDay(0)}
          className={`rounded-md px-3 py-1 font-mono text-xs transition-colors ${
            selectedDay === 0 ? "bg-ink text-mist" : "text-ink-soft hover:text-ink"
          }`}
        >
          {t.all}
        </button>
        {itinerary.days.map((d) => (
          <button
            key={d.day}
            role="tab"
            aria-selected={selectedDay === d.day}
            onClick={() => onSelectDay(d.day)}
            className={`rounded-md px-3 py-1 font-mono text-xs transition-colors ${
              selectedDay === d.day ? "text-white" : "text-ink-soft hover:text-ink"
            }`}
            style={
              selectedDay === d.day
                ? { background: DAY_COLORS[(d.day - 1) % DAY_COLORS.length] }
                : undefined
            }
          >
            {t.day} {d.day}
          </button>
        ))}
      </div>

      <div className="divide-y divide-line/60">
        {visibleDays.map((d) => (
          <div key={d.day} className="px-4 py-3">
            <h3 className="mb-2 flex items-baseline gap-2 font-display font-semibold">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: DAY_COLORS[(d.day - 1) % DAY_COLORS.length] }}
              />
              {t.day} {d.day}
              <span className="font-mono text-xs font-normal text-ink-soft">{d.date}</span>
              {d.weather && (
                <span className="ml-auto font-mono text-xs font-normal text-ink-soft">
                  {weatherEmoji(d.weather.code)} {d.weather.t_max}°/{d.weather.t_min}°
                </span>
              )}
            </h3>
            <ol className="space-y-2">
              {d.items.map((i, idx) => (
                <li key={i.name} className="flex items-baseline gap-3 text-sm">
                  <span className="w-5 text-right font-mono text-xs text-ink-soft">{idx + 1}.</span>
                  <span className="w-12 font-mono text-xs text-ink-soft">{i.start_time}</span>
                  <span className="min-w-0 flex-1">
                    {i.name}{" "}
                    <span className="whitespace-nowrap rounded-sm bg-mist px-1.5 py-px font-mono text-[10px] text-ink-soft">
                      {t.categories[i.category as keyof typeof t.categories] ?? i.category}
                    </span>
                  </span>
                  <span className="whitespace-nowrap font-mono text-xs text-ink-soft">
                    {i.est_cost} {currency}
                  </span>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>

      {itinerary.lodging && (
        <div className="border-t border-line px-4 py-2 text-right font-mono text-xs text-ink-soft">
          {t.lodging}: {itinerary.lodging.nights} {t.nights} × {itinerary.lodging.rooms} {t.rooms} ×{" "}
          {itinerary.lodging.nightly} {currency} = {itinerary.lodging.total} {currency}
        </div>
      )}
      <div className="border-t border-line px-4 py-3 text-right font-mono text-sm">
        {t.totalCost}:{" "}
        <strong>
          {itinerary.total_cost} {currency}
        </strong>
        {rates && (
          <div className="mt-0.5 text-xs text-ink-soft">
            ≈{" "}
            {Object.entries(rates)
              .map(([cur, rate]) => `${(itinerary.total_cost * rate).toFixed(2)} ${cur}`)
              .join(" · ")}
          </div>
        )}
      </div>
    </div>
  );
}
