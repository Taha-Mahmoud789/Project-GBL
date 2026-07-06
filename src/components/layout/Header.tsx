import { Box } from 'lucide-react';

export function Header() {
  return (
    <header className="flex items-center justify-between h-14 px-5 border-b border-border-primary bg-bg-secondary/80 backdrop-blur-md shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/15">
          <Box className="w-5 h-5 text-accent" />
        </div>
        <h1 className="text-base font-semibold tracking-tight text-text-primary">
          Image2Model
        </h1>
        <span className="px-2 py-0.5 text-[10px] font-medium tracking-wider uppercase rounded-full bg-accent/10 text-accent border border-accent/20">
          Beta
        </span>
      </div>
      <nav className="flex items-center gap-1">
        <button className="px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-bg-tertiary rounded-md transition-colors">
          Docs
        </button>
        <button className="px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-bg-tertiary rounded-md transition-colors">
          GitHub
        </button>
      </nav>
    </header>
  );
}
