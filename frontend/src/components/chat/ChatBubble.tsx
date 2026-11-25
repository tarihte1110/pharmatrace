import { useState } from 'react';
import { Check, Clipboard } from 'lucide-react';
import { CitationMessage } from '@/components/chat/CitationMessage';
import type { ChatMessage, SourceCitation } from '@/types/drug';

interface ChatBubbleProps {
  message: ChatMessage;
  selectedSourceId?: number | null;
  onSelectSource: (source: SourceCitation, message: ChatMessage) => void;
}

export function ChatBubble({ message, selectedSourceId, onSelectSource }: ChatBubbleProps) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle');

  async function copyAnswer() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopyState('copied');
    } catch {
      setCopyState('failed');
    }
    window.setTimeout(() => setCopyState('idle'), 2200);
  }

  if (message.role === 'user') {
    return (
      <article className="mx-auto w-full max-w-4xl border-b border-hairline py-4">
        <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="font-mono text-xs font-medium tracking-tight text-muted">
            SORGU • {message.timestamp}
          </span>
          {message.drugTag && (
            <span className="rounded border border-[#B8D4EE] bg-[#EBF3FA] px-2 py-0.5 font-mono text-xs text-navy">
              @ {message.drugTag}
            </span>
          )}
        </div>
        <p className="text-lg font-semibold leading-7 text-primary">{message.content}</p>
      </article>
    );
  }

  const isOutOfScope = message.isPharmaceutical === false;

  return (
    <article className="mx-auto w-full max-w-4xl border-l-[3px] border-navy py-3 pl-4 sm:pl-5">
      <div className="mb-4 flex flex-wrap items-center gap-x-3 gap-y-1">
        <h3 className="font-mono text-xs font-semibold tracking-tight text-navy">
          KLİNİK RAPOR
        </h3>
        <span className="font-mono text-xs tracking-tight text-muted">{message.timestamp}</span>
        {message.cached && (
          <span className="font-mono text-xs tracking-tight text-muted">ÖNBELLEK</span>
        )}
        {isOutOfScope && (
          <span className="font-mono text-xs tracking-tight text-secondary">KAPSAM DIŞI</span>
        )}
      </div>

      <CitationMessage
        content={message.content}
        sources={message.sources}
        activeSourceId={selectedSourceId}
        onSelectSource={(source) => onSelectSource(source, message)}
      />

      <div className="mt-4 border-t border-hairline pt-2">
        <button
          type="button"
          onClick={copyAnswer}
          className="inline-flex h-9 items-center gap-2 rounded-md px-2 text-sm font-medium text-cobalt transition-colors hover:bg-subtle"
        >
          {copyState === 'copied' ? <Check className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
          {copyState === 'copied'
            ? 'Kopyalandı'
            : copyState === 'failed'
              ? 'Kopyalama başarısız'
              : 'Raporu Kopyala'}
        </button>
      </div>
    </article>
  );
}
