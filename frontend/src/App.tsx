import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Methodology } from '@/pages/Methodology';
import { Workspace } from '@/pages/Workspace';
import { fetchHealth } from '@/services/api';
import type { HealthResponse } from '@/types/drug';

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState(false);
  const [activeTab, setActiveTab] = useState<'workspace' | 'methodology'>('workspace');
  const [workspaceKey, setWorkspaceKey] = useState(0);
  const [hasConversation, setHasConversation] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setOffline(false);
      })
      .catch(() => setOffline(true));
  }, []);

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-canvas font-sans text-primary antialiased">
      <Header
        health={health}
        offline={offline}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        hasConversation={hasConversation}
        onNewResearch={() => {
          setHasConversation(false);
          setWorkspaceKey((key) => key + 1);
        }}
      />
      {activeTab === 'workspace' ? (
        <Workspace key={workspaceKey} onConversationStart={() => setHasConversation(true)} />
      ) : (
        <Methodology />
      )}
    </div>
  );
}