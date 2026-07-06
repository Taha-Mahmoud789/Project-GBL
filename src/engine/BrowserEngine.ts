import * as THREE from 'three';
import type { ExportOptions } from '@/types';
import type { BaseEngine, EngineAnalysis, EngineResult, ConversionSettings } from './BaseEngine';

function analyzeSVG(svgContent: string): EngineAnalysis {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, 'image/svg+xml');
  const pathCount = doc.querySelectorAll('path, rect, circle, ellipse, polygon, polyline, line').length;
  const groupCount = doc.querySelectorAll('g').length;
  const imageCount = doc.querySelectorAll('image').length;

  const colors: string[] = [];
  doc.querySelectorAll('[fill]').forEach((el) => {
    const fill = el.getAttribute('fill');
    if (fill && fill !== 'none' && !colors.includes(fill)) colors.push(fill);
  });

  const isRaster = imageCount > 0 && pathCount === 0;
  const isMultiLayer = groupCount > 1 || colors.length > 1;

  return {
    type: isRaster ? 'raster' : 'vector',
    layers: groupCount || 1,
    shapes: pathCount,
    colors,
    warnings: [],
    recommendedEngine: isRaster ? 'RASTER_TRACE' : isMultiLayer ? 'SVG_LAYER' : 'SVG_VECTOR',
  };
}

// ponytail: BrowserEngine kept as reference. Heavy processing moved to LocalEngine (server-side).
export class BrowserEngine implements BaseEngine {
  readonly id = 'browser';
  readonly name = 'Browser Engine (fallback)';

  analyze(svgContent: string): EngineAnalysis {
    return analyzeSVG(svgContent);
  }

  async convert(_svgContent: string, _options: ConversionSettings): Promise<EngineResult> {
    throw new Error(
      'BrowserEngine.convert() is disabled. Use LocalEngine (FastAPI server) for SVG-to-3D conversion.',
    );
  }

  async exportGLB(_model: THREE.Group, _options: ExportOptions): Promise<Blob> {
    throw new Error(
      'BrowserEngine.exportGLB() is disabled. Use LocalEngine for server-side GLB export.',
    );
  }
}
