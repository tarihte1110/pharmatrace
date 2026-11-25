import type { ReactNode } from 'react';
import type { SourceCitation } from '@/types/drug';

interface CitationMessageProps {
  content: string;
  sources?: SourceCitation[];
  activeSourceId?: number | null;
  onSelectSource: (source: SourceCitation) => void;
}

interface InlineContext {
  sources: SourceCitation[];
  activeSourceId?: number | null;
  onSelectSource: (source: SourceCitation) => void;
}

function renderInline(text: string, context: InlineContext, keyPrefix: string): ReactNode[] {
  const tokens = text.split(/(\[Kaynak\s+\d+\]|\*\*[^*]+\*\*|\*[^*\n]+\*)/g);

  return tokens.map((token, index) => {
    const key = `${keyPrefix}-${index}`;
    const citation = token.match(/^\[Kaynak\s+(\d+)\]$/);
    if (citation) {
      const sourceId = Number(citation[1]);
      const source = context.sources.find((item) => item.source_id === sourceId);
      const isSelected = context.activeSourceId === sourceId;

      return (
        <button
          key={key}
          type="button"
          disabled={!source}
          onClick={() => source && context.onSelectSource(source)}
          title={source ? `${source.ilac_adi} (${source.dokuman_tipi})` : token}
          className={`mx-0.5 inline-flex translate-y-[-1px] items-center whitespace-nowrap rounded border px-2 py-0.5 font-mono text-[11.5px] font-medium transition-colors ${
            isSelected
              ? 'border-[#06285A] bg-[#06285A] text-white'
              : 'border-[#B8D4EE] bg-[#EBF3FA] text-cobalt hover:border-[#06285A] hover:bg-[#06285A] hover:text-white disabled:cursor-default'
          }`}
        >
          Kaynak {sourceId}
        </button>
      );
    }

    if (token.startsWith('**') && token.endsWith('**')) {
      return (
        <strong key={key} className="font-bold text-primary">
          {token.slice(2, -2)}
        </strong>
      );
    }

    if (token.startsWith('*') && token.endsWith('*')) {
      return <em key={key}>{token.slice(1, -1)}</em>;
    }

    return <span key={key}>{token}</span>;
  });
}

function isListItem(line: string) {
  return /^\s*[-*]\s+/.test(line);
}

function isBlockStart(line: string) {
  return /^\s*(?:#{1,3}\s+|>\s?|[-*]\s+|\d+[.)]\s+|\|.*\|\s*$|---+\s*$)/.test(line);
}

function tableCells(line: string) {
  return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

function isTableSeparator(line: string) {
  return /^\s*\|?[\s:|-]+\|[\s:|-]*\|?\s*$/.test(line) && line.includes('-');
}

function renderMessage(content: string, context: InlineContext) {
  const lines = content.replace(/\r\n?/g, '\n').split('\n');
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const heading = line.match(/^#{1,3}\s+(.+)$/);
    const boldHeading = line.match(/^\*\*(.+)\*\*$/);
    if (heading || boldHeading) {
      const title = (heading?.[1] ?? boldHeading?.[1] ?? '').replace(/[*#]/g, '').trim();
      const isSourceHeading = /^(kaynaklar|sources)$/i.test(title);
      blocks.push(
        <h3
          key={`heading-${index}`}
          className={`font-bold uppercase tracking-[0.04em] text-navy ${
            isSourceHeading
              ? 'mb-2 mt-7 border-b border-hairline pb-2 text-[15px]'
              : 'mb-2 mt-6 text-[15px]'
          }`}
        >
          {renderInline(title, context, `heading-${index}`)}
        </h3>,
      );
      index += 1;
      continue;
    }

    if (/^\s*>\s?/.test(lines[index])) {
      const quoteLines: string[] = [];
      const key = index;
      while (index < lines.length && /^\s*>\s?/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^\s*>\s?/, '').trim());
        index += 1;
      }
      const quoteText = quoteLines.join(' ');
      const isClinicalSummary = /^\*\*Klinik Özet:\*\*/i.test(quoteText);
      blocks.push(
        <blockquote
          key={`quote-${key}`}
          className={`my-4 border-l-4 px-4 py-3 ${
            isClinicalSummary
              ? 'border-cyan bg-subtle text-primary'
              : 'border-strong bg-canvas text-secondary'
          }`}
        >
          {isClinicalSummary && (
            <span className="mb-1.5 block font-mono text-xs font-semibold tracking-tight text-navy">
              Klinik Özet
            </span>
          )}
          <p className="leading-7">
            {renderInline(
              isClinicalSummary ? quoteText.replace(/^\*\*Klinik Özet:\*\*\s*/i, '') : quoteText,
              context,
              `quote-${key}`,
            )}
          </p>
        </blockquote>,
      );
      continue;
    }

    if (
      lines[index].includes('|') &&
      index + 1 < lines.length &&
      isTableSeparator(lines[index + 1])
    ) {
      const headers = tableCells(lines[index]);
      const rows: { cells: string[]; key: number }[] = [];
      const key = index;
      const kaynakIndexes = new Set(
        headers
          .map((header, headerIndex) =>
            header.trim().toLocaleLowerCase('tr-TR') === 'kaynak' ? headerIndex : -1,
          )
          .filter((headerIndex) => headerIndex >= 0),
      );
      index += 2;
      while (index < lines.length && lines[index].trim().startsWith('|')) {
        rows.push({ cells: tableCells(lines[index]), key: index });
        index += 1;
      }

      blocks.push(
        <div key={`table-${key}`} className="my-5 w-full overflow-x-auto border border-hairline">
          <table className="w-full min-w-[560px] border-collapse text-left text-sm">
            <thead className="bg-subtle text-primary">
              <tr>
                {headers.map((header, headerIndex) => (
                  <th key={`header-${headerIndex}`} scope="col" className={`border-b border-hairline px-4 py-3 font-bold ${kaynakIndexes.has(headerIndex) ? 'w-28 whitespace-nowrap text-right' : ''}`}>
                    {renderInline(header, context, `table-${key}-header-${headerIndex}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`row-${row.key}`} className={rowIndex % 2 === 0 ? 'bg-surface' : 'bg-canvas'}>
                  {headers.map((_, cellIndex) => (
                    <td key={`cell-${cellIndex}`} className={`border-b border-hairline px-4 py-3 align-top leading-6 text-secondary last:border-b-0 ${kaynakIndexes.has(cellIndex) ? 'w-28 whitespace-nowrap text-right' : ''}`}>
                      {renderInline(row.cells[cellIndex] ?? '', context, `table-${row.key}-cell-${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    if (isListItem(lines[index])) {
      const items: { text: string; key: number }[] = [];
      while (index < lines.length && isListItem(lines[index])) {
        const key = index;
        const itemLines = [lines[index].replace(/^\s*[-*]\s+/, '').trim()];
        index += 1;

        while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
          itemLines.push(lines[index].trim());
          index += 1;
        }
        items.push({ text: itemLines.join(' '), key });

        while (index < lines.length && !lines[index].trim()) index += 1;
      }

      blocks.push(
        <ul key={`list-${items[0]?.key ?? index}`} className="my-3 list-disc space-y-2 pl-6 marker:text-cobalt">
          {items.map((item) => (
            <li key={`item-${item.key}`} className="pl-1 leading-7">
              {renderInline(item.text, context, `item-${item.key}`)}
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    if (/^\d+[.)]\s+/.test(lines[index])) {
      const items: { text: string; key: number }[] = [];
      while (index < lines.length && /^\d+[.)]\s+/.test(lines[index])) {
        items.push({
          text: lines[index].replace(/^\d+[.)]\s+/, '').trim(),
          key: index,
        });
        index += 1;
      }
      blocks.push(
        <ol key={`ordered-${items[0]?.key ?? index}`} className="my-3 list-decimal space-y-2 pl-6 marker:font-semibold marker:text-cobalt">
          {items.map((item) => (
            <li key={`ordered-item-${item.key}`} className="pl-1 leading-7">
              {renderInline(item.text, context, `ordered-item-${item.key}`)}
            </li>
          ))}
        </ol>,
      );
      continue;
    }

    if (/^\s*---+\s*$/.test(lines[index])) {
      blocks.push(<hr key={`rule-${index}`} className="my-5 border-hairline" />);
      index += 1;
      continue;
    }

    const paragraphLines = [line];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    blocks.push(
      <p key={`paragraph-${index}`} className="my-3 leading-7">
        {renderInline(paragraphLines.join(' '), context, `paragraph-${index}`)}
      </p>,
    );
  }

  return blocks;
}

export function CitationMessage({
  content,
  sources = [],
  activeSourceId,
  onSelectSource,
}: CitationMessageProps) {
  return (
    <div className="max-w-[74ch] break-words text-[15.5px] leading-[1.75] text-reading">
      {renderMessage(content, { sources, activeSourceId, onSelectSource })}
    </div>
  );
}
