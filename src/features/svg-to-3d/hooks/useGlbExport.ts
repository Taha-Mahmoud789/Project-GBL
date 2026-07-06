import { useCallback, useState } from 'react';
import { getEngine } from '@/engine';
import { useLayerStore } from '../store/useLayerStore';
import { buildLayerGroup, validateGlb, downloadBlob } from '@/shared/exporters/glbExporter';
import type { ExportOptions } from '@/types';
import * as THREE from 'three';

export function useGlbExport() {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const layers = useLayerStore((s) => s.layers);

  const exportModel = useCallback(
    async (options: ExportOptions) => {
      if (layers.length === 0) return;

      setIsExporting(true);
      setExportError(null);

      try {
        const engine = getEngine();

        if (engine.id === 'local') {
          await engine.exportGLB(new THREE.Group(), options);
          return;
        }

        const layerPairs = layers
          .filter((l) => l.visible)
          .map((config) => ({ config, shapeData: config.shapeData }));

        const group = buildLayerGroup(layerPairs);
        const blob = await engine.exportGLB(group, options);

        const validation = validateGlb(blob);
        if (!validation.valid) {
          setExportError(validation.error || 'GLB validation failed');
          return;
        }

        const filename = options.filename || 'model.glb';
        downloadBlob(blob, filename.endsWith('.glb') ? filename : `${filename}.glb`);

        group.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.geometry.dispose();
            if (Array.isArray(mesh.material)) {
              mesh.material.forEach((m) => m.dispose());
            } else {
              mesh.material.dispose();
            }
          }
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Unknown export error';
        setExportError(msg);
      } finally {
        setIsExporting(false);
      }
    },
    [layers],
  );

  return { exportModel, isExporting, exportError };
}
