import { useT } from "../../i18n";
import type { Conflict } from "../../hooks/useAgentStatuses";

interface Props {
  conflicts: Conflict[];
}

// Açıq büdcə/logistika konflikti xəbərdarlığı.
// (Qırmızı→yaşıl "konsensus" morph-u sonrakı mərhələdə əlavə olunur.)
export default function ConflictBadge({ conflicts }: Props) {
  const t = useT();
  const open = conflicts.filter((c) => !c.resolved);
  if (open.length === 0) return null;
  const c = open[open.length - 1];

  return (
    <div className="rounded-lg border border-alert/60 bg-alert/10 px-3 py-2 shadow-glow-alert">
      <div className="flex items-center gap-2 font-mono text-[10px] font-semibold tracking-widest text-alert">
        <span aria-hidden>⚠</span>
        {t.conflictDetected}
        <span className="font-normal">R{c.round}</span>
      </div>
    </div>
  );
}
