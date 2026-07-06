import type * as THREE from 'three';
import type { NormalizedShape, ExportOptions } from '@/types';

export interface ConversionSettings {
  depth: number;
  bevel: number;
  smoothness: number;
  mode: 'auto' | 'layered' | 'engraved';
  material: { color: string; metalness: number; roughness: number };
}

export interface EngineAnalysis {
  type: string;
  layers: number;
  shapes: number;
  colors: string[];
  warnings: string[];
  recommendedEngine: string;
}

export interface EngineResult {
  model: THREE.Group;
  layers: NormalizedShape[];
  metadata: Record<string, unknown>;
}

export interface BaseEngine {
  readonly id: string;
  readonly name: string;

  analyze(svgContent: string): EngineAnalysis;

  convert(
    svgContent: string,
    options: ConversionSettings,
  ): Promise<EngineResult>;

  exportGLB(
    model: THREE.Group,
    options: ExportOptions,
  ): Promise<Blob>;
}
