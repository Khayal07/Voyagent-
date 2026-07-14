import type { Itinerary, Trip } from "../types";
import type { LiveProposal } from "../hooks/useLivePoints";

export interface BudgetAllocation {
  lodging: number;
  food: number;
  fun: number;
  reserve: number; // büdcə − xərclənən (mənfi = aşılıb)
  spent: number;
  budget: number;
  over: boolean;
}

// est_cost adambaşınadır: cəm = Σ(items)×nəfər + otel (backend budget agenti ilə eyni düstur)
function allocate(
  items: { category: string; est_cost: number }[],
  travelers: number,
  lodging: number,
  budget: number,
): BudgetAllocation {
  let food = 0;
  let fun = 0;
  for (const it of items) {
    if (it.category === "food") food += it.est_cost;
    else fun += it.est_cost;
  }
  food = Math.round(food * travelers);
  fun = Math.round(fun * travelers);
  const spent = lodging + food + fun;
  return {
    lodging,
    food,
    fun,
    reserve: budget - spent,
    spent,
    budget,
    over: spent > budget,
  };
}

export function budgetFromItinerary(itinerary: Itinerary, trip: Trip): BudgetAllocation {
  return allocate(
    itinerary.days.flatMap((d) => d.items),
    trip.travelers,
    itinerary.lodging?.total ?? 0,
    trip.budget,
  );
}

// Danışıq gedərkən son təklifdən canlı təxmin (otel: gecə × otaq × qiymət)
export function budgetFromLive(live: LiveProposal, trip: Trip): BudgetAllocation {
  const nights = Math.max(
    1,
    Math.round(
      (new Date(trip.end_date).getTime() - new Date(trip.start_date).getTime()) / 86400000,
    ),
  );
  const rooms = Math.ceil(trip.travelers / 2);
  const lodging = live.hotelNightly != null ? Math.round(live.hotelNightly * nights * rooms) : 0;
  return allocate(live.points, trip.travelers, lodging, trip.budget);
}
