import * as THREE from 'three';
import { convertSVGToMesh } from '@image2model/core';
import { buildLayerGroup, exportToGlb } from '@/shared/exporters/glbExporter';
import type { NormalizedShape, LayerConfig, ExportOptions } from '@/types';
import type { BaseEngine, EngineAnalysis, EngineResult, ConversionSettings } from './BaseEngine';
import { generateId } from '@/shared/helpers';

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

export class BrowserEngine implements BaseEngine {
  readonly id = 'browser';
  readonly name = 'Browser Engine';

  analyze(svgContent: string): EngineAnalysis {
    return analyzeSVG(svgContent);
  }

  async convert(svgContent: string, options: ConversionSettings): Promise<EngineResult> {
    const model = await convertSVGToMesh(svgContent, {
      depth: options.depth,
      bevelSize: options.bevel,
      bevelEnabled: options.bevel > 0,
      bevelSegments: options.smoothness,
      steps: 2,
      smoothness: options.smoothness,
      mode: options.mode,
      material: options.material,
    });

    const layers: NormalizedShape[] = [];
    model.traverse((child: THREE.Object3D) => {
      if (child instanceof THREE.Mesh) {
        const mat = child.material as THREE.MeshStandardMaterial;
        const color = mat.color ? '#' + mat.color.getHexString() : '#6366f1';
        layers.push({
          id: generateId(),
          name: `Layer ${layers.length + 1}`,
          shapeData: new THREE.Shape(),
          fillColor: color,
          strokeColor: color,
          opacity: mat.opacity ?? 1,
          zIndex: layers.length,
        });
      }
    });

    return { model, layers, metadata: {} };
  }

  async exportGLB(model: THREE.Group, _options: ExportOptions): Promise<Blob> {
    const layerPairs: Array<{ config: LayerConfig; shapeData: unknown }> = [];
    model.traverse((child: THREE.Object3D) => {
      if (child instanceof THREE.Mesh) {
        const mat = child.material as THREE.MeshStandardMaterial;
        const color = mat.color ? '#' + mat.color.getHexString() : '#6366f1';
        layerPairs.push({
          config: {
            id: generateId(),
            name: child.name || 'Layer',
            fillColor: color,
            opacity: mat.opacity ?? 1,
            zIndex: layerPairs.length,
            depth: 0.5,
            bevelEnabled: true,
            bevelThickness: 0.03,
            bevelSize: 0.03,
            bevelSegments: 2,
            position: [child.position.x, child.position.y, child.position.z],
            rotation: [child.rotation.x, child.rotation.y, child.rotation.z],
            visible: true,
            shapeData: new THREE.Shape(),
          },
          shapeData: new THREE.Shape(),
        });
      }
    });
    const group = buildLayerGroup(layerPairs);
    return await exportToGlb(group);
  }
}
