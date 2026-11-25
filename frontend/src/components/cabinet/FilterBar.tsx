import type { DocumentTypeFilter } from '@/types/drug';

interface FilterBarProps {
  ilacFiltresi: string;
  etkenFiltresi: string;
  documentFilter: DocumentTypeFilter;
  onIlacChange: (val: string) => void;
  onEtkenChange: (val: string) => void;
  onDocumentFilterChange: (filter: DocumentTypeFilter) => void;
}

const DOCUMENT_FILTERS: { value: DocumentTypeFilter; label: string }[] = [
  { value: 'all', label: 'Tümü' },
  { value: 'KÜB', label: 'KÜB' },
  { value: 'KT', label: 'KT' },
];

export function FilterBar({
  ilacFiltresi,
  etkenFiltresi,
  documentFilter,
  onIlacChange,
  onEtkenChange,
  onDocumentFilterChange,
}: FilterBarProps) {
  return (
    <div className="shrink-0 border-b border-hairline bg-canvas px-4 py-2.5 sm:px-6">
      <div className="mx-auto flex max-w-[1800px] flex-wrap items-center gap-2.5">
        <label className="min-w-[180px] flex-1 sm:max-w-[260px]">
          <span className="sr-only">İlaç adına göre filtrele</span>
          <input
            type="text"
            value={ilacFiltresi}
            onChange={(event) => onIlacChange(event.target.value)}
            placeholder="İlaç adına göre filtrele"
            className="h-10 w-full rounded-md border border-strong bg-surface px-3 text-sm text-primary placeholder:text-muted focus:border-cobalt focus:outline-none"
          />
        </label>

        <label className="min-w-[180px] flex-1 sm:max-w-[260px]">
          <span className="sr-only">Etken maddeye göre filtrele</span>
          <input
            type="text"
            value={etkenFiltresi}
            onChange={(event) => onEtkenChange(event.target.value)}
            placeholder="Etken maddeye göre filtrele"
            className="h-10 w-full rounded-md border border-strong bg-surface px-3 text-sm text-primary placeholder:text-muted focus:border-cobalt focus:outline-none"
          />
        </label>

        <div
          role="group"
          aria-label="Belge tipi"
          className="ml-auto inline-flex h-10 shrink-0 items-center border border-strong bg-surface p-0.5"
        >
          {DOCUMENT_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              aria-pressed={documentFilter === filter.value}
              onClick={() => onDocumentFilterChange(filter.value)}
              className={`h-9 min-w-12 px-3 text-sm font-semibold transition-colors ${
                documentFilter === filter.value
                  ? 'bg-navy text-surface'
                  : 'text-secondary hover:bg-subtle hover:text-primary'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {(ilacFiltresi || etkenFiltresi) && (
          <div className="flex w-full flex-wrap gap-2 pt-0.5" aria-label="Etkin filtreler">
            {ilacFiltresi && (
              <button
                type="button"
                onClick={() => onIlacChange('')}
                className="inline-flex min-h-7 items-center gap-2 rounded border border-hairline bg-subtle px-2 font-mono text-xs tracking-tight text-secondary hover:border-strong"
              >
                İLAÇ: {ilacFiltresi}
                <span aria-hidden="true">×</span>
                <span className="sr-only">İlaç filtresini kaldır</span>
              </button>
            )}
            {etkenFiltresi && (
              <button
                type="button"
                onClick={() => onEtkenChange('')}
                className="inline-flex min-h-7 items-center gap-2 rounded border border-hairline bg-subtle px-2 font-mono text-xs tracking-tight text-secondary hover:border-strong"
              >
                ETKEN: {etkenFiltresi}
                <span aria-hidden="true">×</span>
                <span className="sr-only">Etken madde filtresini kaldır</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
