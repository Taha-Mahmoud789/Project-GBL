import { useState } from 'react';
import { Download, X } from 'lucide-react';
import { useGlbExport } from '../hooks/useGlbExport';
import { useLayerStore } from '../store/useLayerStore';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ExportModal({ isOpen, onClose }: ExportModalProps) {
  const [filename, setFilename] = useState('model');
  const [mode, setMode] = useState<'merged' | 'separate'>('separate');
  const { exportModel, isExporting } = useGlbExport();
  const layers = useLayerStore((s) => s.layers);

  if (!isOpen) return null;

  const handleExport = async () => {
    await exportModel({ mode, filename });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-bg-secondary border border-border-primary rounded-lg w-80 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-text-primary">Export GLB</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-2">
          <label className="text-xs text-text-secondary">Filename</label>
          <input
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            className="w-full px-2 py-1.5 text-xs bg-bg-tertiary border border-border-primary rounded text-text-primary"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs text-text-secondary">Mode</label>
          <div className="flex gap-2">
            <button
              onClick={() => setMode('merged')}
              className={`flex-1 px-2 py-1.5 text-xs rounded border ${
                mode === 'merged'
                  ? 'bg-accent/20 border-accent text-accent'
                  : 'border-border-primary text-text-secondary hover:bg-bg-tertiary'
              }`}
            >
              Merged
            </button>
            <button
              onClick={() => setMode('separate')}
              className={`flex-1 px-2 py-1.5 text-xs rounded border ${
                mode === 'separate'
                  ? 'bg-accent/20 border-accent text-accent'
                  : 'border-border-primary text-text-secondary hover:bg-bg-tertiary'
              }`}
            >
              Separate
            </button>
          </div>
        </div>

        <p className="text-[10px] text-text-muted">
          {layers.length} layer{layers.length !== 1 ? 's' : ''} will be exported
          {mode === 'merged' ? ' as one mesh' : ' as separate meshes'}.
        </p>

        <button
          onClick={handleExport}
          disabled={isExporting || layers.length === 0}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded bg-accent text-white hover:bg-accent/90 disabled:opacity-50"
        >
          <Download className="w-3 h-3" />
          {isExporting ? 'Exporting...' : 'Download GLB'}
        </button>
      </div>
    </div>
  );
}
