import { useAppStore } from '@/store';
import { useModelStore } from '@/store/modelStore';
import { useLayerStore } from '@/features/svg-to-3d/store/useLayerStore';
import { Settings, Box, Palette, Download } from 'lucide-react';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { SliderControl } from '@/components/ui/SliderControl';
import { ColorControl } from '@/components/ui/ColorControl';
import { ModeSelector } from '@/components/ui/ModeSelector';

interface ControlsPanelProps {
  onExport?: () => void;
}

export function ControlsPanel({ onExport }: ControlsPanelProps) {
  const {
    materialSettings,
    viewport,
    updateMaterialSettings,
    updateViewport,
  } = useAppStore();

  const {
    uploadedFile,
    fileName,
    fileType,
    fileUrl,
    svgContent,
    modelSettings,
    updateModelSettings,
  } = useModelStore();

  const hasFile = uploadedFile !== null;
  const layers = useLayerStore((s) => s.layers);
  const hasLayers = layers.length > 0;

  return (
    <aside className="flex flex-col w-72 min-w-[288px] h-full border-l border-border-primary bg-bg-panel">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border-primary shrink-0">
        <h2 className="text-sm font-semibold text-text-primary">Controls</h2>
      </div>
      <div className="flex flex-col flex-1 overflow-y-auto">
      {hasFile ? (
        <>
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border-primary shrink-0">
            <div className="w-8 h-8 rounded-md overflow-hidden bg-bg-tertiary shrink-0 border border-border-primary">
              {fileType === 'png' && fileUrl && (
                <img src={fileUrl} alt="" className="w-full h-full object-cover" />
              )}
              {fileType === 'svg' && svgContent && (
                <div
                  className="w-full h-full flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                  dangerouslySetInnerHTML={{ __html: svgContent }}
                />
              )}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{fileName}</p>
              <p className="text-[10px] text-text-muted">{fileType?.toUpperCase()}</p>
            </div>
          </div>

          <div className="flex flex-col">
            <SectionHeader icon={Settings} title="Conversion" />
            <div className="flex flex-col gap-4 px-4 py-3">
              <ModeSelector
                value={modelSettings.mode}
                onChange={(mode) => updateModelSettings({ mode })}
              />

              <SliderControl
                label="Depth"
                value={modelSettings.depth}
                min={0.1}
                max={5}
                step={0.1}
                onChange={(depth) => updateModelSettings({ depth })}
              />

              <SliderControl
                label="Bevel"
                value={modelSettings.bevel}
                min={0}
                max={1}
                step={0.01}
                onChange={(bevel) => updateModelSettings({ bevel })}
              />

              <SliderControl
                label="Smoothness"
                value={modelSettings.smoothness}
                min={1}
                max={10}
                step={1}
                onChange={(smoothness) => updateModelSettings({ smoothness })}
              />
            </div>
          </div>

          <div className="flex flex-col">
            <SectionHeader icon={Palette} title="Material" />
            <div className="flex flex-col gap-4 px-4 py-3">
              <ColorControl
                label="Color"
                value={materialSettings.color}
                onChange={(color) => updateMaterialSettings({ color })}
              />

              <SliderControl
                label="Metalness"
                value={materialSettings.metalness}
                min={0}
                max={1}
                step={0.01}
                onChange={(metalness) => updateMaterialSettings({ metalness })}
              />

              <SliderControl
                label="Roughness"
                value={materialSettings.roughness}
                min={0}
                max={1}
                step={0.01}
                onChange={(roughness) => updateMaterialSettings({ roughness })}
              />
            </div>
          </div>

          <div className="flex flex-col">
            <SectionHeader icon={Box} title="Viewport" />
            <div className="flex flex-col gap-4 px-4 py-3">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-xs text-text-secondary">Show Grid</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={viewport.showGrid}
                    onChange={(e) => updateViewport({ showGrid: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-bg-tertiary rounded-full peer peer-checked:bg-accent/40 transition-colors" />
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-text-muted rounded-full transition-all peer-checked:translate-x-4 peer-checked:bg-accent" />
                </div>
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-xs text-text-secondary">Show Axes</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={viewport.showAxes}
                    onChange={(e) => updateViewport({ showAxes: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-bg-tertiary rounded-full peer peer-checked:bg-accent/40 transition-colors" />
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-text-muted rounded-full transition-all peer-checked:translate-x-4 peer-checked:bg-accent" />
                </div>
              </label>

              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-xs text-text-secondary">Wireframe</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={viewport.wireframe}
                    onChange={(e) => updateViewport({ wireframe: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-bg-tertiary rounded-full peer peer-checked:bg-accent/40 transition-colors" />
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-text-muted rounded-full transition-all peer-checked:translate-x-4 peer-checked:bg-accent" />
                </div>
              </label>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-text-secondary">Background</label>
                <div className="flex gap-2">
                  {([
                    { label: 'Dark', color: '#050505' },
                    { label: 'Gray', color: '#808080' },
                    { label: 'Light', color: '#eeeeee' },
                  ] as const).map((preset) => (
                    <button
                      key={preset.color}
                      onClick={() => updateViewport({ backgroundColor: preset.color })}
                      className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-[10px] font-medium rounded-md border transition-all ${
                        viewport.backgroundColor === preset.color
                          ? 'border-accent/50 bg-accent/15 text-accent'
                          : 'border-border-primary bg-bg-secondary text-text-muted hover:border-border-secondary'
                      }`}
                    >
                      <div
                        className="w-2.5 h-2.5 rounded-full border border-border-primary"
                        style={{ backgroundColor: preset.color }}
                      />
                      {preset.label}
                    </button>
                  ))}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-text-muted">Custom</span>
                  <input
                    type="color"
                    value={viewport.backgroundColor}
                    onChange={(e) => updateViewport({ backgroundColor: e.target.value })}
                    className="w-6 h-6 rounded border border-border-primary cursor-pointer bg-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          {hasLayers && onExport && (
            <div className="px-4 py-3 border-t border-border-primary">
              <button
                onClick={onExport}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded bg-accent text-white hover:bg-accent/90"
              >
                <Download className="w-3 h-3" />
                Export GLB
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full px-6 text-center">
          <div className="w-12 h-12 rounded-xl bg-bg-tertiary flex items-center justify-center mb-4">
            <Settings className="w-6 h-6 text-text-muted" />
          </div>
          <p className="text-sm font-medium text-text-secondary mb-1">No file uploaded</p>
          <p className="text-xs text-text-muted">
            Upload an SVG file to convert it to a 3D model
          </p>
        </div>
      )}
      </div>
    </aside>
  );
}
