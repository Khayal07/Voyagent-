import { useEffect, useState } from "react";
import { getRates } from "./api";

// Valyuta başına bir fetch — nəticə modul səviyyəsində paylaşılır
const cache = new Map<string, Promise<Record<string, number> | null>>();

function fetchRates(base: string): Promise<Record<string, number> | null> {
  if (!cache.has(base)) {
    cache.set(
      base,
      getRates(base)
        .then((r) => r.rates)
        .catch(() => {
          cache.delete(base);
          return null;
        }),
    );
  }
  return cache.get(base)!;
}

/** Trip valyutasından qalan valyutalara məzənnələr; yüklənməyib/xəta → null. */
export function useRates(base: string): Record<string, number> | null {
  const [rates, setRates] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    let alive = true;
    fetchRates(base).then((r) => {
      if (alive) setRates(r);
    });
    return () => {
      alive = false;
    };
  }, [base]);

  return rates;
}
