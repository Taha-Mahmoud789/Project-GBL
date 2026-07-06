import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  uploadPanel: ReactNode;
  viewer: ReactNode;
  controlsPanel: ReactNode;
}

export function Layout({ uploadPanel, viewer, controlsPanel }: LayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-bg-primary">
      <Header />
      <main className="flex flex-1 min-h-0">
        <Sidebar side="left" title="Images">
          {uploadPanel}
        </Sidebar>
        {viewer}
        {controlsPanel}
      </main>
    </div>
  );
}
