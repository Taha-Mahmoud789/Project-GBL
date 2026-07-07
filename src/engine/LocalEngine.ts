import * as THREE from 'three';
import type { NormalizedShape, ExportOptions } from '@/types';
import type { BaseEngine, EngineAnalysis, EngineResult, ConversionSettings } from './BaseEngine';
import { parseGlbBytes } from '@/shared/exporters/glbImporter';
import { generateId } from '@/shared/helpers';

export class LocalEngine implements BaseEngine {
  readonly id = 'local';
  readonly name = 'Local Engine (FastAPI)';

  private readonly baseUrl: string;

  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  async analyze(svgContent: string): Promise<EngineAnalysis> {
    const res = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ svg_content: svgContent }),
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Analyze failed (${res.status}): ${detail}`);
    }

    const data = await res.json();
    return {
      type: data.type,
      layers: data.layers,
      shapes: data.shapes,
      colors: data.colors,
      warnings: data.warnings,
      recommendedEngine: data.recommended_engine,
    };
  }

  async convert(
    svgContent: string,
    options: ConversionSettings,
    onProgress?: (progress: number, message: string) => void,
  ): Promise<EngineResult> {
    // Start conversion
    const res = await fetch(`${this.baseUrl}/convert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        svg_content: svgContent,
        settings: {
          depth: options.depth,
          bevel: options.bevel,
          smoothness: options.smoothness,
          mode: options.mode,
        },
        material: {
          color: options.material.color,
          metalness: options.material.metalness,
          roughness: options.material.roughness,
        },
      }),
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Convert failed (${res.status}): ${detail}`);
    }

    // Poll progress if task id is returned
    const taskId = res.headers.get('X-Task-Id');
    if (taskId && onProgress) {
      this.pollProgress(taskId, onProgress).catch(() => {});
    }

    // Parse GLB response
    const buffer = await res.arrayBuffer();
    if (buffer.byteLength === 0) {
      throw new Error('Server returned empty GLB');
    }

    const model = await parseGlbBytes(buffer);

    // Extract layer info from the model
    const layers: NormalizedShape[] = [];
    model.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const mat = child.material as THREE.MeshStandardMaterial;
        const color = mat.color ? '#' + mat.color.getHexString() : '#6366f1';
        layers.push({
          id: generateId(),
          name: child.name || `Layer ${layers.length + 1}`,
          shapeData: new THREE.Shape(),
          fillColor: color,
          strokeColor: color,
          opacity: mat.opacity ?? 1,
          zIndex: layers.length,
        });
      }
    });

    return { model, layers, metadata: { taskId } };
  }

  async exportGLB(_model: THREE.Group, _options: ExportOptions): Promise<Blob> {
    // GLB is already exported by the server during convert().
    // For re-export with different settings, call convert() again.
    throw new Error('Use convert() to get GLB from server. Direct exportGLB not yet supported.');
  }

  /**
   * Check if the FastAPI server is reachable.
   */
  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  private async pollProgress(
    taskId: string,
    onProgress: (progress: number, message: string) => void,
  ): Promise<void> {
    const url = `${this.baseUrl}/progress/${taskId}/stream`;
    const res = await fetch(url);
    if (!res.ok || !res.body) return;

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Parse SSE lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          onProgress(data.progress, data.message);
          if (data.status === 'completed' || data.status === 'failed') return;
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}
