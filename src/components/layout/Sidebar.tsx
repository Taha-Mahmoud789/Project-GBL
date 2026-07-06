import type { ReactNode } from 'react';

interface SidebarProps {
  side: 'left' | 'right';
  title: string;
  count?: number;
  children: ReactNode;
}

export function Sidebar({ side, title, count, children }: SidebarProps) {
  return (
    <aside
      className={`flex flex-col w-72 min-w-[288px] h-full bg-bg-panel ${
        side === 'left'
          ? 'border-r border-border-primary'
          : 'border-l border-border-primary'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-primary shrink-0">
        <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
        {count !== undefined && (
          <span className="text-xs text-text-muted">{count} file(s)</span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </aside>
  );
}
