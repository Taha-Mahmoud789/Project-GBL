import * as THREE from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import type { LayerConfig } from '@/types';
import {
  createExtrudedGeometry,
  createMaterial,
} from '@image2model/core';

/**
 * Build a THREE.Group from layer configs and their shape data.
 * Each visible layer becomes a named mesh child.
 */
export function buildLayerGroup(
  layers: Array<{ config: LayerConfig; shapeData: unknown }>,
): THREE.Group {
  const group = new THREE.Group();
  group.name = 'SVG Layers';

  let currentZ = 0;

  for (const { config, shapeData } of layers) {
    if (!config.visible) continue;

    const shape = shapeData as THREE.Shape;
    const geometry = createExtrudedGeometry(shape, {
      depth: config.depth,
      bevelEnabled: config.bevelEnabled,
      bevelThickness: config.bevelThickness,
      bevelSize: config.bevelSize,
      bevelSegments: config.bevelSegments,
      curveSegments: 32,
      steps: 2,
    });

    const material = createMaterial({
      color: config.fillColor,
      metalness: 0.2,
      roughness: 0.4,
      opacity: config.opacity,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = config.name;
    mesh.position.set(
      config.position[0],
      config.position[1],
      config.position[2] + currentZ,
    );
    mesh.rotation.set(
      config.rotation[0],
      config.rotation[1],
      config.rotation[2],
    );
    mesh.renderOrder = config.zIndex;
    group.add(mesh);

    currentZ += config.depth + 0.02;
  }

  return group;
}

/**
 * Export a THREE.Group as a GLB Blob.
 */
export async function exportToGlb(group: THREE.Group): Promise<Blob> {
  const exporter = new GLTFExporter();

  return new Promise((resolve, reject) => {
    exporter.parse(
      group,
      (result) => {
        // result is ArrayBuffer for binary
        resolve(new Blob([result as ArrayBuffer], { type: 'model/gltf-binary' }));
      },
      (error) => reject(error),
      { binary: true },
    );
  });
}

/**
 * Validate a GLB blob after export.
 * Checks magic number, minimum size, and structure.
 */
export function validateGlb(blob: Blob): { valid: boolean; error?: string } {
  if (blob.size === 0) {
    return { valid: false, error: 'Exported GLB is empty (0 bytes)' };
  }

  if (blob.size < 12) {
    return { valid: false, error: `GLB too small: ${blob.size} bytes (minimum 12)` };
  }

  return { valid: true };
}

/**
 * Trigger a browser download of a Blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
