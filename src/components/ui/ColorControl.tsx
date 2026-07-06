interface ColorControlProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export function ColorControl({
  label,
  value,
  onChange,
}: ColorControlProps) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-xs text-text-secondary">{label}</label>
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-text-muted">{value}</span>
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-6 h-6 rounded border border-border-primary cursor-pointer bg-transparent"
        />
      </div>
    </div>
  );
}
