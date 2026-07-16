import type { Itinerary, ItineraryItem, Trip } from "../types";
import { budgetFromItinerary } from "./budget";

export interface OptimizeResult {
  itinerary: Itinerary;
  removed: string[]; // çıxarılan yerlərin adları (baha → ucuz sırası)
  changed: boolean;
}

// est_cost adambaşınadır → cəmi backend budget agenti ilə eyni düsturla hesablanır
function totalCost(days: Itinerary["days"], travelers: number, lodging: number): number {
  const activities = days.reduce(
    (sum, d) => sum + d.items.reduce((s, i) => s + i.est_cost, 0),
    0,
  );
  return Math.round(activities * travelers + lodging);
}

// Deterministik "nə olardı" simulyasiyası: hədəf büdcəyə sığmaq üçün ən baha
// qeyri-yemək item-larını (əyləncə/attraksion) bir-bir atır. Hər gündə ən azı
// bir yer saxlanır; yemək və otel toxunulmazdır. LLM çağırışı YOXDUR.
export function optimizeForBudget(
  itinerary: Itinerary,
  trip: Trip,
  targetBudget: number,
): OptimizeResult {
  const lodging = itinerary.lodging?.total ?? 0;

  if (budgetFromItinerary(itinerary, trip).spent <= targetBudget) {
    return { itinerary, removed: [], changed: false };
  }

  // İşlək kopya — orijinala toxunmadan item-ları çıxarırıq
  const days = itinerary.days.map((d) => ({ ...d, items: [...d.items] }));
  const working: Itinerary = { ...itinerary, days };
  const removed: string[] = [];

  while (budgetFromItinerary(working, trip).spent > targetBudget) {
    // Ən baha çıxarıla bilən item-i tap (gündə ən azı 1 yer qalmalı)
    let best: { items: ItineraryItem[]; item: ItineraryItem } | null = null;
    for (const d of days) {
      if (d.items.length <= 1) continue;
      for (const it of d.items) {
        if (it.category === "food") continue;
        if (!best || it.est_cost > best.item.est_cost) best = { items: d.items, item: it };
      }
    }
    if (!best) break; // daha çıxarıla bilən yer qalmadı
    best.items.splice(best.items.indexOf(best.item), 1);
    removed.push(best.item.name);
  }

  working.total_cost = totalCost(days, trip.travelers, lodging);
  return { itinerary: working, removed, changed: removed.length > 0 };
}
