import type { ConversionMode } from '@/types';

const MODE_OPTIONS: { value: ConversionMode; label: string; description: string }[] = [
  { value: 'auto', label: 'Auto', description: 'Detect from SVG colors' },
  { value: 'layered', label: 'Layered', description: 'Raise each color as a layer' },
  { value: 'engraved', label: 'Engraved', description: 'Keep holes and cutouts' },
];

interface ModeSelectorProps {
  value: ConversionMode;
  onChange: (value: ConversionMode) => void;
}

export function ModeSelector({
  value,
  onChange,
}: ModeSelectorProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-text-secondary">SVG Mode</label>
      <div className="flex gap-1.5">
        {MODE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            title={opt.description}
            className={`flex-1 px-2 py-1.5 text-[10px] font-medium rounded-md border transition-all ${
              value === opt.value
                ? 'border-accent/50 bg-accent/15 text-accent'
                : 'border-border-primary bg-bg-secondary text-text-muted hover:border-border-secondary'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
