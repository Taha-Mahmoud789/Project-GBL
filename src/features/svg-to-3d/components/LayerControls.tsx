import { useLayerStore } from '../store/useLayerStore';
import { SliderControl } from '@/components/ui/SliderControl';
import { ColorControl } from '@/components/ui/ColorControl';

export function LayerControls({ layerId }: { layerId: string }) {
  const layer = useLayerStore((s) => s.layers.find((l) => l.id === layerId));
  const updateLayer = useLayerStore((s) => s.updateLayer);

  if (!layer) return null;

  const patch = (partial: Record<string, unknown>) =>
    updateLayer(layerId, partial);

  return (
    <div className="px-4 pb-3 space-y-3">
      <ColorControl
        label="Color"
        value={layer.fillColor}
        onChange={(v) => patch({ fillColor: v })}
      />

      <SliderControl
        label="Depth"
        value={layer.depth}
        min={0.01}
        max={3}
        step={0.01}
        onChange={(v) => patch({ depth: v })}
      />

      <div className="space-y-2">
        <label className="text-xs text-text-secondary flex items-center gap-2">
          <input
            type="checkbox"
            checked={layer.bevelEnabled}
            onChange={(e) => patch({ bevelEnabled: e.target.checked })}
            className="accent-accent"
          />
          Bevel
        </label>
        {layer.bevelEnabled && (
          <>
            <SliderControl
              label="Bevel Thickness"
              value={layer.bevelThickness}
              min={0}
              max={0.5}
              step={0.005}
              onChange={(v) => patch({ bevelThickness: v })}
            />
            <SliderControl
              label="Bevel Size"
              value={layer.bevelSize}
              min={0}
              max={0.5}
              step={0.005}
              onChange={(v) => patch({ bevelSize: v })}
            />
            <SliderControl
              label="Bevel Segments"
              value={layer.bevelSegments}
              min={1}
              max={8}
              step={1}
              onChange={(v) => patch({ bevelSegments: v })}
            />
          </>
        )}
      </div>

      <div className="space-y-2">
        <span className="text-xs text-text-secondary">Position</span>
        {(['x', 'y', 'z'] as const).map((axis, i) => (
          <SliderControl
            key={axis}
            label={axis.toUpperCase()}
            value={layer.position[i]}
            min={-5}
            max={5}
            step={0.01}
            onChange={(v) => {
              const pos = [...layer.position] as [number, number, number];
              pos[i] = v;
              patch({ position: pos });
            }}
          />
        ))}
      </div>

      <div className="space-y-2">
        <span className="text-xs text-text-secondary">Rotation</span>
        {(['x', 'y', 'z'] as const).map((axis, i) => (
          <SliderControl
            key={axis}
            label={axis.toUpperCase()}
            value={layer.rotation[i]}
            min={-Math.PI}
            max={Math.PI}
            step={0.01}
            onChange={(v) => {
              const rot = [...layer.rotation] as [number, number, number];
              rot[i] = v;
              patch({ rotation: rot });
            }}
          />
        ))}
      </div>
    </div>
  );
}
