import { useState } from "react";
import type { TripInput } from "../types";

const INTEREST_OPTIONS = ["tarix", "təbiət", "yemək", "gecə həyatı", "incəsənət", "alış-veriş"];
const MAX_DAYS = 5;

interface Props {
  onSubmit: (input: TripInput) => void;
  busy: boolean;
}

export default function TripForm({ onSubmit, busy }: Props) {
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
    if (isNaN(days) || days < 1) return setError("Tarix aralığı düzgün deyil.");
    if (days > MAX_DAYS) return setError(`Maksimum ${MAX_DAYS} günlük səyahət dəstəklənir.`);
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
      <h2 className="font-display text-2xl font-extrabold tracking-tight">Hara gedirik?</h2>
      <p className="mb-6 mt-1 text-sm text-ink-soft">
        Detalları ver — dörd agent sənin üçün ən yaxşı marşrutu müzakirə etsin.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className={label} htmlFor="city">Şəhər</label>
          <input id="city" className={field} required minLength={2} placeholder="məs. Roma"
            value={city} onChange={(e) => setCity(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="start">Başlama</label>
          <input id="start" type="date" className={field} required
            value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="end">Bitmə</label>
          <input id="end" type="date" className={field} required
            value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <div>
          <label className={label} htmlFor="budget">Büdcə</label>
          <div className="flex gap-2">
            <input id="budget" type="number" min={1} className={field} required placeholder="500"
              value={budget} onChange={(e) => setBudget(e.target.value)} />
            <select
              aria-label="Valyuta"
              className="rounded-md border border-line bg-card px-2 text-sm outline-none focus:border-ink"
              value={currency} onChange={(e) => setCurrency(e.target.value)}
            >
              {["USD", "EUR", "AZN"].map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className={label} htmlFor="travelers">Nəfər</label>
          <input id="travelers" type="number" min={1} max={20} className={field} required
            value={travelers} onChange={(e) => setTravelers(Number(e.target.value))} />
        </div>
        <div className="sm:col-span-2">
          <span className={label}>Maraqlar</span>
          <div className="flex flex-wrap gap-2">
            {INTEREST_OPTIONS.map((i) => {
              const active = interests.includes(i);
              return (
                <button
                  key={i} type="button" onClick={() => toggleInterest(i)} aria-pressed={active}
                  className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "border-ink bg-ink text-mist"
                      : "border-line bg-card text-ink-soft hover:border-ink-soft"
                  }`}
                >
                  {i}
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
        {busy ? "Agentlər danışır..." : "Marşrutu planla"}
      </button>
    </form>
  );
}
