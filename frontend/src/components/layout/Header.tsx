import { RotateCcw } from 'lucide-react';
import brandLogo from '@/assets/logo/logo.png';
import type { HealthResponse } from '@/types/drug';

interface HeaderProps {
  health: HealthResponse | null;
  offline: boolean;
  activeTab: 'workspace' | 'methodology';
  hasConversation: boolean;
  onTabChange: (tab: 'workspace' | 'methodology') => void;
  onNewResearch: () => void;
}

export function Header({
  health,
  offline,
  activeTab,
  hasConversation,
  onTabChange,
  onNewResearch,
}: HeaderProps) {
  return (
    <header className="relative z-20 h-16 shrink-0 border-b border-hairline bg-surface px-4 sm:px-6">
      <div className="mx-auto flex h-full max-w-[1800px] items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3 lg:gap-8">
          <div className="flex shrink-0 items-center gap-2.5">
            <img src={brandLogo} alt="" className="h-10 w-auto object-contain" />
            <div className="min-w-0">
              <h1 className="text-lg font-bold leading-6 tracking-tight text-primary">
                PharmaTrace
              </h1>
              <p className="mt-0.5 hidden font-mono text-[10px] tracking-tight text-muted md:block">
                KÜB / KT KLİNİK ARŞİVİ
              </p>
            </div>
          </div>

          <nav aria-label="Ana gezinme" className="flex h-full shrink-0 items-center gap-4 sm:gap-6">
            <button
              type="button"
              aria-current={activeTab === 'workspace' ? 'page' : undefined}
              onClick={() => onTabChange('workspace')}
              className={`h-full border-b-2 px-1 text-sm font-semibold transition-colors ${
                activeTab === 'workspace'
                  ? 'border-navy text-navy'
                  : 'border-transparent text-secondary hover:text-primary'
              }`}
            >
              <span>Araştırma</span>
            </button>
            <button
              type="button"
              aria-current={activeTab === 'methodology' ? 'page' : undefined}
              onClick={() => onTabChange('methodology')}
              className={`h-full border-b-2 px-1 text-sm font-semibold transition-colors ${
                activeTab === 'methodology'
                  ? 'border-navy text-navy'
                  : 'border-transparent text-secondary hover:text-primary'
              }`}
            >
              <span className="hidden xl:inline">Sistem Mimarisi</span>
              <span className="xl:hidden">Mimari</span>
            </button>
          </nav>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          {health && !offline && (
            <span className="hidden whitespace-nowrap font-mono text-xs tracking-tight text-secondary md:inline">
              {health.indexed_chunks.toLocaleString('tr-TR')} BÖLÜM
            </span>
          )}
          <span
            title={offline ? 'Hizmet erişilemiyor' : health ? health.model : 'Durum kontrol ediliyor'}
            className="inline-flex items-center gap-2 whitespace-nowrap text-xs font-medium text-secondary"
          >
            <span className={`h-2 w-2 rounded-full ${offline ? 'bg-muted' : health ? 'bg-online' : 'bg-muted'}`} />
            <span className="hidden sm:inline">
              {offline ? 'Hizmet erişilemiyor' : health ? 'Hizmet aktif' : 'Durum kontrol ediliyor'}
            </span>
          </span>

          {activeTab === 'workspace' && hasConversation && (
            <button
              type="button"
              onClick={onNewResearch}
              className="inline-flex h-10 items-center gap-2 rounded-md bg-navy px-3 text-sm font-semibold text-surface transition-colors hover:bg-cobalt sm:px-4"
            >
              <RotateCcw className="h-4 w-4" />
              <span className="hidden sm:inline">Yeni Araştırma</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
