import { useEffect, useRef, useState } from 'react';
import { ChevronDown, ChevronUp, X } from 'lucide-react';
import type { DocumentTypeFilter, SourceCitation } from '@/types/drug';

interface SourceDrawerProps {
  sources: SourceCitation[];
  citedSourceIds: number[];
  selectedSource: SourceCitation | null;
  documentFilter: DocumentTypeFilter;
  onSelectSource: (source: SourceCitation) => void;
  onClose?: () => void;
}

function matchesDocumentFilter(source: SourceCitation, filter: DocumentTypeFilter) {
  if (filter === 'all') return true;
  const documentType = source.dokuman_tipi.toLocaleUpperCase('tr-TR').replace('Ü', 'U');
  return filter === 'KÜB' ? documentType.includes('KUB') : documentType.includes('KT');
}

function documentBadgeClass(source: SourceCitation) {
  if (matchesDocumentFilter(source, 'KT')) {
    return 'border-[#A5F3FC] bg-[#ECFEFF] text-[#0E7490]';
  }
  return 'border-[#B8D4EE] bg-[#EBF3FA] text-navy';
}

export function SourceDrawer({
  sources,
  citedSourceIds,
  selectedSource,
  documentFilter,
  onSelectSource,
  onClose,
}: SourceDrawerProps) {
  const [expandedSourceId, setExpandedSourceId] = useState<number | null>(null);
  const sourceRefs = useRef<Record<number, HTMLElement | null>>({});
  const citedIds = new Set(citedSourceIds);
  const visibleSources = sources.filter((source) => matchesDocumentFilter(source, documentFilter));
  const citedSources = visibleSources.filter((source) => citedIds.has(source.source_id));
  const otherSources = visibleSources.filter((source) => !citedIds.has(source.source_id));

  useEffect(() => {
    const sourceId = selectedSource?.source_id;
    if (
      sourceId === undefined ||
      !selectedSource ||
      !matchesDocumentFilter(selectedSource, documentFilter)
    ) return;

    setExpandedSourceId(sourceId);
    const scrollTimer = window.setTimeout(() => {
      sourceRefs.current[sourceId]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 60);
    return () => window.clearTimeout(scrollTimer);
  }, [selectedSource, documentFilter]);

  function renderSource(source: SourceCitation) {
    const isSelected = selectedSource?.source_id === source.source_id;
    const isExpanded = expandedSourceId === source.source_id;
    const fullText = source.full_text || source.excerpt;

    return (
      <article
        key={source.source_id}
        ref={(element) => {
          sourceRefs.current[source.source_id] = element;
        }}
        className={`border-b border-hairline border-l-2 ${
          isSelected ? 'border-l-cobalt bg-surface' : 'border-l-transparent'
        }`}
      >
        <button
          type="button"
          aria-pressed={isSelected}
          onClick={() => onSelectSource(source)}
          className="block w-full px-3 pb-3 pt-4 text-left"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-mono text-xs font-medium tracking-tight text-muted">
              KAYNAK {source.source_id}
            </span>
            <span className="font-mono text-xs tracking-tight text-secondary">
              RRF {source.score.toFixed(3)}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <h4 className="text-sm font-bold leading-5 text-primary">{source.ilac_adi}</h4>
            <span className={`inline-flex min-h-6 items-center rounded border px-2 font-mono text-xs tracking-tight ${documentBadgeClass(source)}`}>
              {source.dokuman_tipi}
            </span>
          </div>
          {source.etken_maddeler.length > 0 && (
            <p className="mt-1.5 text-xs leading-5 text-secondary">
              <span className="font-semibold text-primary">Etken madde:</span>{' '}
              {source.etken_maddeler.join(', ')}
            </p>
          )}
        </button>

        <div className="px-3 pb-2">
          <p className={`whitespace-pre-line break-words text-[13.5px] leading-[1.7] text-[#334155] ${isExpanded ? '' : 'line-clamp-4'}`}>
            {isExpanded ? fullText : source.excerpt}
          </p>
          <button
            type="button"
            aria-expanded={isExpanded}
            onClick={() => setExpandedSourceId(isExpanded ? null : source.source_id)}
            className="mt-2 inline-flex min-h-9 items-center gap-2 text-sm font-semibold text-cobalt hover:text-navy"
          >
            <span>{isExpanded ? 'Metni Daralt' : 'Tam Metni Göster'}</span>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </article>
    );
  }

  return (
    <aside className="flex h-full min-h-0 flex-col border-l border-hairline bg-canvas">
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-hairline px-6 py-5">
        <div>
          <h2 className="text-sm font-bold text-primary">Prospektüs inceleyici</h2>
          <p className="mt-1 font-mono text-xs tracking-tight text-muted">
            {visibleSources.length} EŞLEŞEN BÖLÜM
          </p>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Kaynak panelini kapat"
            className="flex h-9 w-9 items-center justify-center rounded-md text-secondary hover:bg-subtle"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <div className="chat-scroll min-h-0 flex-1 overflow-y-auto px-6 pb-8">
        {visibleSources.length === 0 ? (
          <div className="border-b border-hairline px-1 py-5">
            <p className="text-sm font-semibold text-primary">
              {sources.length === 0 ? 'Henüz kaynak yok' : 'Bu belge türünde kaynak bulunamadı'}
            </p>
            <p className="mt-1.5 text-sm leading-6 text-secondary">
              {sources.length === 0
                ? 'Bir klinik sorgu gönderdiğinizde eşleşen KÜB ve KT bölümleri burada görünür.'
                : 'Belge türü filtresini değiştirerek diğer eşleşmeleri görüntüleyin.'}
            </p>
          </div>
        ) : (
          <div>
            <section aria-labelledby="cited-sources-heading">
              <div className="flex items-center justify-between gap-3 border-b border-hairline py-3">
                <h3 id="cited-sources-heading" className="font-mono text-xs font-semibold tracking-tight text-navy">
                  Yanıtta Atıf Yapılanlar
                </h3>
                <span className="font-mono text-xs tracking-tight text-muted">
                  {citedSources.length}
                </span>
              </div>
              {citedSources.length > 0 ? (
                citedSources.map(renderSource)
              ) : (
                <p className="border-b border-hairline px-1 py-3 text-sm text-secondary">
                  Bu yanıtta kaynak atfı bulunmuyor.
                </p>
              )}
            </section>

            {otherSources.length > 0 && (
              <section aria-labelledby="other-sources-heading" className="mt-5">
                <div className="flex items-center justify-between gap-3 border-b border-hairline py-3">
                  <h3 id="other-sources-heading" className="font-mono text-xs font-semibold tracking-tight text-secondary">
                    Diğer Eşleşen Bölümler
                  </h3>
                  <span className="font-mono text-xs tracking-tight text-muted">
                    {otherSources.length}
                  </span>
                </div>
                {otherSources.map(renderSource)}
              </section>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
