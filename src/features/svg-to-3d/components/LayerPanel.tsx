import { useState } from 'react';
import { Eye, EyeOff, ChevronDown, ChevronRight, Layers } from 'lucide-react';
import { useLayerStore } from '../store/useLayerStore';
import { LayerControls } from './LayerControls';
import { SectionHeader } from '@/components/ui/SectionHeader';
import type { LayerConfig } from '@/types';

export function LayerPanel() {
  const layers = useLayerStore((s) => s.layers);
  const toggleVisibility = useLayerStore((s) => s.toggleVisibility);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (layers.length === 0) {
    return (
      <div className="p-4 text-center text-text-muted text-xs">
        <Layers className="w-8 h-8 mx-auto mb-2 opacity-40" />
        Upload an SVG to see layers
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <SectionHeader icon={Layers} title={`Layers (${layers.length})`} />
      <div className="flex-1 overflow-y-auto">
        {layers.map((layer) => (
          <LayerItem
            key={layer.id}
            layer={layer}
            isExpanded={expandedId === layer.id}
            onToggleExpand={() =>
              setExpandedId(expandedId === layer.id ? null : layer.id)
            }
            onToggleVisibility={() => toggleVisibility(layer.id)}
          />
        ))}
      </div>
    </div>
  );
}

function LayerItem({
  layer,
  isExpanded,
  onToggleExpand,
  onToggleVisibility,
}: {
  layer: LayerConfig;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onToggleVisibility: () => void;
}) {
  return (
    <div className="border-b border-border-primary">
      <div className="flex items-center gap-2 px-3 py-2 hover:bg-bg-secondary/50">
        <button onClick={onToggleExpand} className="text-text-muted">
          {isExpanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
        </button>
        <div
          className="w-3 h-3 rounded-sm border border-border-primary"
          style={{ backgroundColor: layer.fillColor }}
        />
        <span className="flex-1 text-xs text-text-primary truncate">
          {layer.name}
        </span>
        <button onClick={onToggleVisibility} className="text-text-muted">
          {layer.visible ? (
            <Eye className="w-3 h-3" />
          ) : (
            <EyeOff className="w-3 h-3 opacity-40" />
          )}
        </button>
      </div>
      {isExpanded && <LayerControls layerId={layer.id} />}
    </div>
  );
}
