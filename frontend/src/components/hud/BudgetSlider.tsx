import { useT } from "../../i18n";

interface Props {
  min: number;
  max: number;
  value: number;
  spent: number; // simulyasiya olunan xərc
  currency: string;
  removedCount: number;
  changed: boolean;
  applying: boolean;
  applied: boolean;
  onChange: (value: number) => void;
  onApply: () => void;
  onReset: () => void;
  onCompare: () => void;
}

// Büdcə "nə olardı" simulyatoru: sürgü büdcəni sıxdıqca ən baha yerlər planı
// canlı tərk edir. Tətbiq mövcud PATCH endpoint-i ilə saxlanır (LLM yox).
export default function BudgetSlider({
  min,
  max,
  value,
  spent,
  currency,
  removedCount,
  changed,
  applying,
  applied,
  onChange,
  onApply,
  onReset,
  onCompare,
}: Props) {
  const t = useT();

  return (
    <div className="hud-panel w-52 px-3 py-2.5">
      <div className="mb-1.5 font-mono text-[9px] font-medium tracking-[0.18em] text-muted">
        {t.budgetSim}
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={Math.max(1, Math.round((max - min) / 100))}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={t.budgetSimHint}
        className="w-full accent-[var(--color-primary)]"
      />

      <div className="mt-1 flex items-baseline justify-between font-mono text-[10px]">
        <span className="text-primary-deep">
          {Math.round(value)} {currency}
        </span>
        <span className={spent > value ? "text-alert" : "text-muted"}>
          → {Math.round(spent)}
        </span>
      </div>

      <p className="mt-1 font-mono text-[9px] leading-tight text-muted">
        {changed ? `${removedCount} ${t.removedLabel.toLowerCase()}` : t.noChanges}
      </p>

      <div className="mt-2 flex gap-1.5">
        <button
          onClick={onApply}
          disabled={!changed || applying || applied}
          className="flex-1 rounded-md border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-primary-deep transition-colors hover:bg-surface disabled:opacity-40"
        >
          {applied ? `✓ ${t.applied}` : applying ? "…" : t.applyPlan}
        </button>
        <button
          onClick={onCompare}
          disabled={!changed}
          className="rounded-md border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:bg-surface hover:text-ink disabled:opacity-40"
        >
          A/B
        </button>
        <button
          onClick={onReset}
          className="rounded-md border border-line px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted transition-colors hover:bg-surface hover:text-ink"
        >
          {t.resetPlan}
        </button>
      </div>
    </div>
  );
}
