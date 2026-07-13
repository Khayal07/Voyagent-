import { useState } from "react";
import { INTEREST_KEYS, useT } from "../i18n";
import type { TripInput } from "../types";

const MAX_DAYS = 5;

interface Props {
  onSubmit: (input: Omit<TripInput, "language">) => void;
  busy: boolean;
}

export default function TripForm({ onSubmit, busy }: Props) {
  const t = useT();
  const [city, setCity] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [travelers, setTravelers] = useState(2);
  const [interests, setInterests] = useState<string[]>([]);
  const [error, setError] = useState("");

  const toggleInterest = (i: string) =>
    setInterests((prev) => (prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const days = (new Date(endDate).getTime() - new Date(startDate).getTime()) / 86400000 + 1;
    if (isNaN(days) || days < 1) return setError(t.errDates);
    if (days > MAX_DAYS) return setError(t.errMaxDays.replace("{n}", String(MAX_DAYS)));
    onSubmit({
      city: city.trim(),
      start_date: startDate,
      end_date: endDate,
      budget: Number(budget),
      currency,
      travelers,
      interests,
    });
  };

  const field =
    "w-full rounded-md border border-line bg-card px-3 py-2 text-sm outline-none focus:border-ink focus:ring-2 focus:ring-ink/15";
  const label = "mb-1 block font-mono text-[11px] tracking-wider text-ink-soft uppercase";

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-line bg-card p-6 shadow-[0_1px_0_var(--color-line)]"
    >
      <h2 className="font-display text-2xl font-extrabold tracking-tight">{t.formTitle}</h2>
      <p className="mb-6 mt-1 text-sm text-ink-soft">{t.formSubtitle}</p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className={label} htmlFor="city">{t.city}</label>
          <input id="city" className={field} required minLength={2} placeholder={t.cityPlaceholder}
            value={city} onChange={(e) => setCity(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="start">{t.startDate}</label>
          <input id="start" type="date" className={field} required
            value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="end">{t.endDate}</label>
          <input id="end" type="date" className={field} required
            value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="budget">{t.budget}</label>
          <div className="flex gap-2">
            <input id="budget" type="number" min={1} className={field} required placeholder="500"
              value={budget} onChange={(e) => setBudget(e.target.value)} />
            <select
              aria-label={t.currency}
              className="rounded-md border border-line bg-card px-2 text-sm outline-none focus:border-ink"
              value={currency} onChange={(e) => setCurrency(e.target.value)}
            >
              {["USD", "EUR", "AZN"].map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className={label} htmlFor="travelers">{t.travelers}</label>
          <input id="travelers" type="number" min={1} max={20} className={field} required
            value={travelers} onChange={(e) => setTravelers(Number(e.target.value))} />
        </div>
        <div className="sm:col-span-2">
          <span className={label}>{t.interests}</span>
          <div className="flex flex-wrap gap-2">
            {INTEREST_KEYS.map((key) => {
              const active = interests.includes(key);
              return (
                <button
                  key={key} type="button" onClick={() => toggleInterest(key)} aria-pressed={active}
                  className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "border-ink bg-ink text-mist"
                      : "border-line bg-card text-ink-soft hover:border-ink-soft"
                  }`}
                >
                  {t.interestLabels[key]}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {error && <p className="mt-4 text-sm text-route">{error}</p>}

      <button
        type="submit" disabled={busy}
        className="mt-6 w-full rounded-md bg-route px-4 py-3 font-display text-base font-semibold text-white transition-colors hover:bg-route-deep disabled:opacity-50"
      >
        {busy ? t.submitBusy : t.submit}
      </button>
    </form>
  );
}
