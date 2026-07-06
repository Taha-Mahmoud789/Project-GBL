import type { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  icon: LucideIcon;
  title: string;
}

export function SectionHeader({ icon: Icon, title }: SectionHeaderProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 border-b border-border-primary">
      <Icon className="w-4 h-4 text-accent" />
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
    </div>
  );
}
