import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { arrayMove, SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useState } from "react";
import { patchItinerary } from "../api";
import { useT } from "../i18n";
import type { Itinerary, ItineraryItem } from "../types";
import { useRates } from "../useRates";
import { weatherEmoji } from "../weather";
import { DAY_COLORS } from "./MapView";
import PoiThumb from "./PoiThumb";

interface Props {
  itinerary: Itinerary;
  currency: string;
  selectedDay: number;
  onSelectDay: (day: number) => void;
  tripId?: string | null;
  editable?: boolean;
  onChange?: (it: Itinerary) => void;
  onError?: (message: string) => void;
}

const SEP = "::";

function SortableItem({
  item,
  idx,
  day,
  currency,
  editable,
  saving,
  canDelete,
  onDelete,
}: {
  item: ItineraryItem;
  idx: number;
  day: number;
  currency: string;
  editable: boolean;
  saving: boolean;
  canDelete: boolean;
  onDelete: () => void;
}) {
  const t = useT();
  const id = `${day}${SEP}${item.name}`;
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id,
    disabled: !editable || saving,
  });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`group flex items-center gap-3 text-sm ${isDragging ? "z-10 opacity-70" : ""} ${
        editable && !saving ? "cursor-grab active:cursor-grabbing" : ""
      }`}
      {...attributes}
      {...listeners}
    >
      <span className="w-5 text-right font-mono text-xs text-ink-soft">{idx + 1}.</span>
      <span className="w-12 font-mono text-xs text-ink-soft">{item.start_time}</span>
      <PoiThumb wiki={item.wiki} name={item.name} />
      <span className="min-w-0 flex-1">
        {item.name}{" "}
        <span className="whitespace-nowrap rounded-sm bg-mist px-1.5 py-px font-mono text-[10px] text-ink-soft">
          {t.categories[item.category as keyof typeof t.categories] ?? item.category}
        </span>
      </span>
      <span className="whitespace-nowrap font-mono text-xs text-ink-soft">
        {item.est_cost} {currency}
      </span>
      {editable && canDelete && (
        <button
          aria-label={`${t.deleteItem}: ${item.name}`}
          title={t.deleteItem}
          disabled={saving}
          onPointerDown={(e) => e.stopPropagation()}
          onClick={onDelete}
          className="rounded px-1 font-mono text-xs text-ink-soft opacity-0 transition-opacity hover:text-route group-hover:opacity-100"
        >
          ✕
        </button>
      )}
    </li>
  );
}

export default function ItineraryPanel({
  itinerary,
  currency,
  selectedDay,
  onSelectDay,
  tripId,
  editable = false,
  onChange,
  onError,
}: Props) {
  const t = useT();
  const rates = useRates(currency);
  const [saving, setSaving] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor),
  );

  const visibleDays =
    selectedDay === 0 ? itinerary.days : itinerary.days.filter((d) => d.day === selectedDay);
  const totalItems = itinerary.days.reduce((n, d) => n + d.items.length, 0);
  const canEdit = editable && !!tripId && !!onChange;

  const save = async (names: Map<number, string[]>) => {
    if (!tripId || !onChange) return;
    setSaving(true);
    try {
      const updated = await patchItinerary(
        tripId,
        itinerary.days.map((d) => ({ day: d.day, items: names.get(d.day) ?? d.items.map((i) => i.name) })),
      );
      onChange(updated);
    } catch {
      onError?.(t.updateFailed);
    } finally {
      setSaving(false);
    }
  };

  const currentNames = () =>
    new Map(itinerary.days.map((d) => [d.day, d.items.map((i) => i.name)]));

  const handleDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const [fromDayS, fromName] = String(active.id).split(SEP);
    const [toDayS, toName] = String(over.id).split(SEP);
    const fromDay = Number(fromDayS);
    const toDay = Number(toDayS);

    const names = currentNames();
    const src = [...(names.get(fromDay) ?? [])];
    const fromIdx = src.indexOf(fromName);
    if (fromIdx < 0) return;

    if (fromDay === toDay) {
      // arrayMove — aşağı sürüşdürəndə hədəfin ARXASINA düşür (dnd-kit semantikası)
      const toIdx = toName ? src.indexOf(toName) : src.length - 1;
      if (toIdx < 0 || toIdx === fromIdx) return;
      names.set(fromDay, arrayMove(src, fromIdx, toIdx));
    } else {
      src.splice(fromIdx, 1);
      const dst = [...(names.get(toDay) ?? [])];
      const toIdx = toName ? dst.indexOf(toName) : dst.length;
      dst.splice(toIdx < 0 ? dst.length : toIdx, 0, fromName);
      names.set(fromDay, src);
      names.set(toDay, dst);
    }
    void save(names);
  };

  const handleDelete = (day: number, name: string) => {
    const names = currentNames();
    names.set(day, (names.get(day) ?? []).filter((n) => n !== name));
    void save(names);
  };

  const body = (
    <div className={`divide-y divide-line/60 ${saving ? "pointer-events-none opacity-60" : ""}`}>
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
          <SortableContext
            items={d.items.map((i) => `${d.day}${SEP}${i.name}`)}
            strategy={verticalListSortingStrategy}
          >
            <ol className="space-y-2">
              {d.items.map((i, idx) => (
                <SortableItem
                  key={i.name}
                  item={i}
                  idx={idx}
                  day={d.day}
                  currency={currency}
                  editable={canEdit}
                  saving={saving}
                  canDelete={totalItems > 1}
                  onDelete={() => handleDelete(d.day, i.name)}
                />
              ))}
            </ol>
          </SortableContext>
        </div>
      ))}
    </div>
  );

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

      {canEdit ? (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
          {body}
        </DndContext>
      ) : (
        body
      )}

      {canEdit && (
        <div className="border-t border-line px-4 py-1.5 font-mono text-[10px] text-ink-soft">
          {t.dragHint}
        </div>
      )}

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
