import { useEffect, useRef, useCallback } from 'react';
import { useModelStore } from '@/store/modelStore';
import { useLayerStore } from '../store/useLayerStore';
import { getEngine, checkServerHealth } from '@/engine';

interface PipelineState {
  isConverting: boolean;
  error: string | null;
}

export function useConversionPipeline() {
  const svgContent = useModelStore((s) => s.svgContent);
  const modelSettings = useModelStore((s) => s.modelSettings);
  const setGeneratedModel = useModelStore((s) => s.setGeneratedModel);
  const setSvgAnalysis = useModelStore((s) => s.setSvgAnalysis);
  const setLayersFromShapes = useLayerStore((s) => s.setLayersFromShapes);
  const stateRef = useRef<PipelineState>({
    isConverting: false,
    error: null,
  });
  const lastSvg = useRef<string | null>(null);

  // Check server health on mount
  useEffect(() => {
    checkServerHealth().then((ok) => {
      console.log(`[Engine] Server available: ${ok}`);
    });
  }, []);

  const runPipeline = useCallback(async (svg: string) => {
    stateRef.current = { isConverting: true, error: null };

    try {
      const engine = await getEngine();

      // Run analysis first
      const analysis = await engine.analyze(svg);
      setSvgAnalysis({
        type: analysis.type,
        stats: { paths: analysis.shapes, fills: analysis.colors.length, strokes: 0, images: 0, texts: 0, masks: 0, filters: 0 },
        recommendedEngine: analysis.recommendedEngine,
        warnings: analysis.warnings,
      });

      // Convert
      const { model, layers } = await engine.convert(svg, modelSettings);

      if (model.children.length > 0) {
        setGeneratedModel(model);
        setLayersFromShapes(layers);
      } else {
        stateRef.current.error = 'Conversion produced no geometry';
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      stateRef.current.error = msg;
      console.error('[Pipeline]', err);
    } finally {
      stateRef.current.isConverting = false;
    }
  }, [setGeneratedModel, setLayersFromShapes, setSvgAnalysis, modelSettings]);

  useEffect(() => {
    if (svgContent && svgContent !== lastSvg.current) {
      lastSvg.current = svgContent;
      runPipeline(svgContent);
    }
  }, [svgContent, runPipeline]);

  return {
    isConverting: stateRef.current.isConverting,
    error: stateRef.current.error,
  };
}
