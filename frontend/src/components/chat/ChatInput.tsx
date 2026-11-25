import { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { AtSign, ArrowRight, LoaderCircle, X } from 'lucide-react';
import { fetchDrugCatalog } from '@/services/api';
import type { DrugCatalogEntry } from '@/types/drug';

interface ChatInputProps {
  value: string;
  loading: boolean;
  taggedDrug: DrugCatalogEntry | null;
  onChange: (val: string) => void;
  onTaggedDrugChange: (drug: DrugCatalogEntry | null) => void;
  onSubmit: (e: FormEvent) => void;
}

function normalizeSearch(value: string) {
  return value.trim().toLocaleLowerCase('tr-TR');
}

export function ChatInput({
  value,
  loading,
  taggedDrug,
  onChange,
  onTaggedDrugChange,
  onSubmit,
}: ChatInputProps) {
  const [catalog, setCatalog] = useState<DrugCatalogEntry[] | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [suggestionsDismissed, setSuggestionsDismissed] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const catalogRequestStarted = useRef(false);

  const mentionMatch = value.match(/(?:^|\s)@([^\s@]*)$/);
  const mentionQuery = mentionMatch?.[1] ?? '';
  const isMentionActive = mentionMatch !== null;
  const showSuggestions = isMentionActive && !suggestionsDismissed;

  useEffect(() => {
    if (!isMentionActive || catalog !== null || catalogError || catalogRequestStarted.current) return;

    catalogRequestStarted.current = true;
    setCatalogLoading(true);
    fetchDrugCatalog()
      .then(setCatalog)
      .catch((error: unknown) => {
        catalogRequestStarted.current = false;
        setCatalogError(error instanceof Error ? error.message : 'İlaç kataloğu alınamadı.');
      })
      .finally(() => setCatalogLoading(false));
  }, [isMentionActive, catalog, catalogError]);

  useEffect(() => {
    setHighlightedIndex(0);
  }, [mentionQuery]);

  const suggestions = useMemo(() => {
    if (!catalog) return [];
    const query = normalizeSearch(mentionQuery);
    return catalog
      .filter((drug) => {
        if (!query) return true;
        return (
          normalizeSearch(drug.ilac_adi).includes(query) ||
          drug.etken_maddeler.some((ingredient) => normalizeSearch(ingredient).includes(query))
        );
      })
      .slice(0, 8);
  }, [catalog, mentionQuery]);

  function chooseDrug(drug: DrugCatalogEntry) {
    if (!mentionMatch) return;
    onChange(value.slice(0, mentionMatch.index).trimEnd());
    onTaggedDrugChange(drug);
    setSuggestionsDismissed(false);
    inputRef.current?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!showSuggestions) return;

    if (event.key === 'ArrowDown' && suggestions.length > 0) {
      event.preventDefault();
      setHighlightedIndex((index) => (index + 1) % suggestions.length);
    } else if (event.key === 'ArrowUp' && suggestions.length > 0) {
      event.preventDefault();
      setHighlightedIndex((index) => (index - 1 + suggestions.length) % suggestions.length);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (suggestions[highlightedIndex]) chooseDrug(suggestions[highlightedIndex]);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      setSuggestionsDismissed(true);
    }
  }

  return (
    <form onSubmit={onSubmit} className="shrink-0 border-t border-hairline bg-surface px-4 py-4 sm:px-6">
      <div className="mx-auto max-w-4xl">
        {taggedDrug && (
          <div className="mb-3 flex items-center justify-between gap-3 rounded-md border border-[#B8D4EE] bg-[#EBF3FA] px-3 py-2.5">
            <div className="flex min-w-0 items-center gap-2.5">
              <AtSign className="h-4 w-4 shrink-0 text-navy" />
              <div className="min-w-0">
                <p className="truncate text-sm font-bold text-primary">{taggedDrug.ilac_adi}</p>
                {taggedDrug.etken_maddeler.length > 0 && (
                  <p className="truncate text-xs text-secondary">{taggedDrug.etken_maddeler.join(', ')}</p>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onTaggedDrugChange(null)}
              aria-label="Etiketlenen ilacı kaldır"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-navy hover:bg-subtle"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="relative">
          {showSuggestions && (
            <div
              id="drug-suggestions"
              role="listbox"
              aria-label="İlaç önerileri"
              className="absolute bottom-full left-0 z-30 mb-3 max-h-[min(26rem,65vh)] w-full overflow-y-auto rounded-md border border-hairline bg-surface shadow-lg sm:max-w-2xl"
            >
              <div className="sticky top-0 flex items-center justify-between gap-3 border-b border-hairline bg-surface px-4 py-3">
                <p className="text-sm font-bold text-primary">İlaç kataloğunda ara</p>
                <span className="font-mono text-xs tracking-tight text-muted">↑ ↓ gezin · Enter seçin · Esc kapatın</span>
              </div>

              {catalogLoading && (
                <div className="flex items-center gap-2 px-4 py-5 text-sm text-secondary">
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                  İlaç kataloğu yükleniyor…
                </div>
              )}

              {catalogError && (
                <div className="flex items-center justify-between gap-4 px-4 py-4 text-sm text-secondary">
                  <span>{catalogError}</span>
                  <button
                    type="button"
                    onClick={() => setCatalogError(null)}
                    className="h-9 shrink-0 rounded-md border border-strong px-3 font-semibold underline-offset-2 hover:bg-subtle"
                  >
                    Yeniden dene
                  </button>
                </div>
              )}

              {!catalogLoading && !catalogError && suggestions.length === 0 && (
                <p className="px-4 py-5 text-sm text-secondary">Eşleşen ilaç bulunamadı.</p>
              )}

              {suggestions.map((drug, index) => (
                <button
                  key={drug.ilac_adi}
                  id={`drug-option-${index}`}
                  type="button"
                  role="option"
                  aria-selected={highlightedIndex === index}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => chooseDrug(drug)}
                  className={`flex min-h-[68px] w-full items-center justify-between gap-4 border-b border-hairline px-4 py-3.5 text-left last:border-b-0 ${
                    highlightedIndex === index ? 'bg-subtle' : 'hover:bg-canvas'
                  }`}
                >
                  <span className="text-sm font-semibold leading-5 text-primary">{drug.ilac_adi}</span>
                  {drug.etken_maddeler.length > 0 && (
                    <span className="max-w-[55%] text-right text-xs leading-5 text-secondary">
                      {drug.etken_maddeler.join(', ')}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          <div className="flex min-h-[64px] items-center gap-3 rounded-md border border-strong bg-surface px-3 transition-colors focus-within:border-cobalt sm:px-4">
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(event) => {
                onChange(event.target.value);
                setSuggestionsDismissed(false);
              }}
              onKeyDown={handleKeyDown}
              aria-label="Klinik soru"
              aria-autocomplete="list"
              aria-controls={showSuggestions ? 'drug-suggestions' : undefined}
              aria-expanded={showSuggestions}
              aria-activedescendant={
                showSuggestions && suggestions[highlightedIndex]
                  ? `drug-option-${highlightedIndex}`
                  : undefined
              }
              placeholder="Klinik soruyu yazın… İlaç etiketlemek için @ kullanın"
              className="h-12 min-w-0 flex-1 bg-transparent text-base text-primary placeholder:text-muted focus:outline-none"
            />
            <button
              type="submit"
              disabled={loading || !value.trim() || isMentionActive}
              aria-label="Aramayı başlat"
              className="inline-flex h-11 shrink-0 items-center gap-2 rounded-md bg-navy px-4 text-sm font-bold text-surface transition-colors hover:bg-cobalt disabled:cursor-not-allowed disabled:bg-strong"
            >
              <span className="hidden sm:inline">Araştır</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
        <p className="mt-2 text-xs leading-5 text-secondary">
          <strong className="text-primary">@</strong> ile katalogdan ilaç seçin. Yanıtlar resmi KÜB / KT kaynaklarına dayanır.
        </p>
      </div>
    </form>
  );
}
