import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { FilterBar } from '@/components/cabinet/FilterBar';
import { SourceDrawer } from '@/components/cabinet/SourceDrawer';
import { ChatBubble } from '@/components/chat/ChatBubble';
import { ChatInput } from '@/components/chat/ChatInput';
import { sendChatQuery } from '@/services/api';
import type {
  ChatMessage,
  DocumentTypeFilter,
  DrugCatalogEntry,
  SourceCitation,
} from '@/types/drug';

const QUICK_TOPICS = [
  {
    label: 'Doz Aşımı',
    question: 'Parasetamol doz aşımında toksisite bulguları ve başvuru eşikleri nelerdir?',
  },
  {
    label: 'Gebelik & Laktasyon',
    question: 'Gebelik ve emzirme döneminde bu ilacın kullanımına ilişkin prospektüs bilgisi nedir?',
  },
  {
    label: 'Böbrek / Karaciğer',
    question: 'Böbrek veya karaciğer yetmezliğinde doz ayarlaması nasıl yapılır?',
  },
  {
    label: 'Etkileşimler',
    question: 'Bu ilacın kontrendikasyonları ve önemli ilaç etkileşimleri nelerdir?',
  },
];

const SAMPLE_QUESTIONS = [
  {
    eyebrow: 'GÜVENLİLİK / DOZ',
    question: 'Parasetamol yüksek dozda karaciğeri nasıl etkiler?',
  },
  {
    eyebrow: 'ÖZEL POPÜLASYON',
    question: 'Gebelikte hangi ağrı kesiciler kullanılmamalıdır?',
  },
  {
    eyebrow: 'DOZ AYARLAMASI',
    question: 'Böbrek yetmezliğinde doz ayarlaması gerekir mi?',
  },
];

interface WorkspaceProps {
  onConversationStart: () => void;
}

function getCitedSourceIds(answer: string) {
  const sourceIds = new Set<number>();
  const citationPattern = /\[Kaynak\s+(\d+)\]/g;
  let match: RegExpExecArray | null;

  while ((match = citationPattern.exec(answer)) !== null) {
    sourceIds.add(Number(match[1]));
  }

  return [...sourceIds];
}

function matchesDocumentFilter(source: SourceCitation, filter: DocumentTypeFilter) {
  if (filter === 'all') return true;
  const documentType = source.dokuman_tipi.toLocaleUpperCase('tr-TR').replace('Ü', 'U');
  return filter === 'KÜB' ? documentType.includes('KUB') : documentType.includes('KT');
}

export function Workspace({ onConversationStart }: WorkspaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [ilacFiltresi, setIlacFiltresi] = useState('');
  const [etkenFiltresi, setEtkenFiltresi] = useState('');
  const [documentFilter, setDocumentFilter] = useState<DocumentTypeFilter>('all');
  const [taggedDrug, setTaggedDrug] = useState<DrugCatalogEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);
  const [citedSourceIds, setCitedSourceIds] = useState<number[]>([]);
  const [selectedSource, setSelectedSource] = useState<SourceCitation | null>(null);
  const [mobileSourcesOpen, setMobileSourcesOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (messages.length === 0 && !loading) return;
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function handleAsk(questionText: string, drugTag = taggedDrug) {
    const trimmed = questionText.trim();
    if (!trimmed || loading) return;

    onConversationStart();
    setError(null);
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
      drugTag: drugTag?.ilac_adi,
      timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setTaggedDrug(null);
    setLoading(true);

    try {
      const response = await sendChatQuery({
        question: trimmed,
        ilac_filtresi: drugTag?.ilac_adi || ilacFiltresi,
        etken_madde_filtresi: etkenFiltresi,
        dokuman_tipi: documentFilter === 'all' ? null : documentFilter === 'KÜB' ? 'KUB' : 'KT',
      });

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        isPharmaceutical: response.is_pharmaceutical,
        cached: response.cached,
        timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setActiveSources(response.sources);
      const sourceIds = getCitedSourceIds(response.answer);
      setCitedSourceIds(sourceIds);
      setSelectedSource(
        response.sources.find((source) => sourceIds.includes(source.source_id)) ??
          response.sources[0] ??
          null,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Beklenmeyen bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    handleAsk(input, taggedDrug);
  }

  const hasSources = activeSources.length > 0;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <FilterBar
        ilacFiltresi={ilacFiltresi}
        etkenFiltresi={etkenFiltresi}
        documentFilter={documentFilter}
        onIlacChange={setIlacFiltresi}
        onEtkenChange={setEtkenFiltresi}
        onDocumentFilterChange={setDocumentFilter}
      />

      <div
        className={`mx-auto grid min-h-0 w-full max-w-[1800px] flex-1 grid-cols-1 overflow-hidden ${
          hasSources ? 'lg:grid-cols-[minmax(0,1fr)_440px] xl:grid-cols-[minmax(0,1fr)_480px]' : ''
        }`}
      >
        <section className="flex min-h-0 min-w-0 flex-col overflow-hidden">
          <div className="chat-scroll min-h-0 flex-1 space-y-6 overflow-y-auto px-4 py-6 pb-10 sm:px-8 sm:py-8 sm:pb-12">
            {messages.length === 0 && (
              <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col justify-start py-4 sm:py-8">
                <p className="font-mono text-xs font-medium tracking-tight text-cobalt">
                  TİTCK RESMİ KÜB &amp; KT ARŞİVİ
                </p>
                <h2 className="mt-4 max-w-3xl text-4xl font-bold tracking-tight text-primary">
                  Prospektüs Araştırma
                </h2>
                <p className="mt-3 max-w-3xl text-base leading-7 text-secondary">
                  Resmi ürün bilgisi ve kullanma talimatlarında klinik yanıtları kaynaklarıyla inceleyin.
                </p>

                <div className="mt-8">
                  <h3 className="mb-3 font-mono text-xs font-semibold tracking-tight text-muted">
                    KLİNİK KATEGORİLER
                  </h3>
                  <div className="grid grid-cols-1 border-l border-t border-hairline sm:grid-cols-2">
                    {QUICK_TOPICS.map(({ label, question }) => (
                      <button
                        key={label}
                        type="button"
                        onClick={() => handleAsk(question)}
                        className="min-h-12 border-b border-r border-hairline px-4 py-4 text-left text-sm font-semibold text-primary transition-colors hover:bg-subtle"
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-8">
                  <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="font-mono text-xs font-semibold tracking-tight text-muted">
                      ÖRNEK KLİNİK SORULAR
                    </h3>
                    <span className="text-xs text-muted">Bir soruyu seçerek araştırmayı başlatın</span>
                  </div>
                  <div className="border-t border-hairline">
                    {SAMPLE_QUESTIONS.map(({ eyebrow, question }) => (
                      <button
                        key={question}
                        type="button"
                        onClick={() => handleAsk(question)}
                        className="grid w-full gap-1 border-b border-hairline px-3 py-4 text-left transition-colors hover:bg-subtle sm:grid-cols-[180px_minmax(0,1fr)] sm:items-center sm:gap-4"
                      >
                        <span className="font-mono text-xs tracking-tight text-muted">
                          {eyebrow}
                        </span>
                        <span className="text-sm font-medium leading-6 text-primary">
                          {question}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                <p className="mt-7 border-t border-hairline pt-4 text-xs leading-5 text-muted">
                  PharmaTrace resmi prospektüs kayıtlarında bilgi erişimi sağlar; klinik değerlendirme ve tedavi kararlarının yerini almaz.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <ChatBubble
                key={message.id}
                message={message}
                selectedSourceId={selectedSource?.source_id}
                onSelectSource={(source, sourceMessage) => {
                  setActiveSources(sourceMessage.sources ?? []);
                  setCitedSourceIds(getCitedSourceIds(sourceMessage.content));
                  setSelectedSource(source);
                  if (!matchesDocumentFilter(source, documentFilter)) {
                    setDocumentFilter('all');
                  }
                  setMobileSourcesOpen(true);
                }}
              />
            ))}

            {loading && (
              <div className="mx-auto flex w-full max-w-4xl items-center gap-3 border-y border-hairline py-4 text-sm font-medium text-secondary">
                <Loader2 className="h-5 w-5 animate-spin text-cobalt" />
                <span>Resmi kaynaklar taranıyor, klinik yanıt hazırlanıyor…</span>
              </div>
            )}

            {error && (
              <div role="alert" className="mx-auto flex w-full max-w-4xl items-start gap-3 border-y border-hairline py-4 text-sm font-medium leading-6 text-secondary">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-cobalt" />
                <span>{error}</span>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          <ChatInput
            value={input}
            loading={loading}
            taggedDrug={taggedDrug}
            onChange={setInput}
            onTaggedDrugChange={setTaggedDrug}
            onSubmit={onSubmit}
          />
        </section>

        {hasSources && (
          <section className="hidden min-h-0 overflow-hidden lg:block">
            <SourceDrawer
              sources={activeSources}
              citedSourceIds={citedSourceIds}
              selectedSource={selectedSource}
              documentFilter={documentFilter}
              onSelectSource={setSelectedSource}
            />
          </section>
        )}
      </div>

      {mobileSourcesOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Kaynak panelini kapat"
            onClick={() => setMobileSourcesOpen(false)}
            className="absolute inset-0 h-full w-full bg-primary/40"
          />
          <div className="absolute inset-y-0 right-0 w-[min(100vw,480px)]">
            <SourceDrawer
              sources={activeSources}
              citedSourceIds={citedSourceIds}
              selectedSource={selectedSource}
              documentFilter={documentFilter}
              onSelectSource={setSelectedSource}
              onClose={() => setMobileSourcesOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
