import { useT } from "../i18n";
import type { Itinerary, Trip } from "../types";
import { useRates } from "../useRates";
import { weatherEmoji } from "../weather";

interface Props {
  trip: Trip;
  itinerary: Itinerary;
}

/** Yalnız çap üçün görünən səhifə — window.print() ilə PDF-ə çevrilir. */
export default function PrintableItinerary({ trip, itinerary }: Props) {
  const t = useT();
  const rates = useRates(trip.currency);

  return (
    <div className="print-only px-2 font-sans text-[13px] text-black">
      <h1 className="font-display text-2xl font-extrabold">
        Voyagent — {trip.city}
      </h1>
      <p className="mb-4 font-mono text-xs">
        {trip.start_date} → {trip.end_date} · {trip.travelers} {t.people} · {t.budget}:{" "}
        {trip.budget} {trip.currency}
      </p>

      {itinerary.days.map((d) => (
        <div key={d.day} className="mb-3" style={{ breakInside: "avoid" }}>
          <h2 className="border-b border-black pb-1 font-display text-base font-bold">
            {t.day} {d.day} — {d.date}
            {d.weather && (
              <span className="ml-2 font-mono text-xs font-normal">
                {weatherEmoji(d.weather.code)} {d.weather.t_max}°/{d.weather.t_min}°
              </span>
            )}
          </h2>
          <table className="w-full border-collapse">
            <tbody>
              {d.items.map((i, idx) => (
                <tr key={i.name} className="border-b border-gray-300">
                  <td className="w-6 py-1 font-mono text-xs">{idx + 1}.</td>
                  <td className="w-14 py-1 font-mono text-xs">{i.start_time}</td>
                  <td className="py-1">{i.name}</td>
                  <td className="w-20 py-1 font-mono text-xs">
                    {t.categories[i.category as keyof typeof t.categories] ?? i.category}
                  </td>
                  <td className="w-20 py-1 text-right font-mono text-xs">
                    {i.est_cost} {trip.currency}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {itinerary.lodging && (
        <p className="text-right font-mono text-xs">
          {t.lodging}: {itinerary.lodging.nights} {t.nights} × {itinerary.lodging.rooms} {t.rooms} ×{" "}
          {itinerary.lodging.nightly} {trip.currency} = {itinerary.lodging.total} {trip.currency}
        </p>
      )}
      <p className="mt-1 text-right font-mono text-sm font-bold">
        {t.totalCost}: {itinerary.total_cost} {trip.currency}
        {rates && (
          <span className="ml-2 font-normal">
            (≈{" "}
            {Object.entries(rates)
              .map(([cur, rate]) => `${(itinerary.total_cost * rate).toFixed(2)} ${cur}`)
              .join(" · ")}
            )
          </span>
        )}
      </p>

      <p className="mt-6 border-t border-gray-400 pt-2 text-[10px] text-gray-600">
        Rates by exchangerate-api.com · Weather by open-meteo.com · Map data © OpenStreetMap
        contributors · Places via Geoapify · Images via Wikipedia
      </p>
    </div>
  );
}
