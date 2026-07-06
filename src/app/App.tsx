import { useState } from 'react';
import { Layout } from '@/components/layout';
import { UploadPanel } from '@/features/upload';
import { Viewer3D } from '@/features/viewer';
import { ControlsPanel } from '@/components/controls';
import { LayerPanel, ExportModal } from '@/features/svg-to-3d';
import { useLayerStore } from '@/features/svg-to-3d/store/useLayerStore';
import { useConversionPipeline } from '@/features/svg-to-3d/hooks/useConversionPipeline';

function App() {
  const [showExport, setShowExport] = useState(false);
  const layers = useLayerStore((s) => s.layers);
  useConversionPipeline();

  return (
    <>
      <Layout
        uploadPanel={
          <div className="flex flex-col h-full">
            <UploadPanel />
            {layers.length > 0 && <LayerPanel />}
          </div>
        }
        viewer={<Viewer3D />}
        controlsPanel={<ControlsPanel onExport={() => setShowExport(true)} />}
      />
      <ExportModal isOpen={showExport} onClose={() => setShowExport(false)} />
    </>
  );
}

export default App;
