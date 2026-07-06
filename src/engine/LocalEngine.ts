import * as THREE from 'three';
import type { ExportOptions } from '@/types';
import type { BaseEngine, EngineAnalysis, EngineResult, ConversionSettings } from './BaseEngine';

export class LocalEngine implements BaseEngine {
  readonly id = 'local';
  readonly name = 'Local Engine (FastAPI)';

  private readonly baseUrl: string;

  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    void this.baseUrl;
  }

  analyze(_svgContent: string): EngineAnalysis {
    throw new Error('LocalEngine.analyze() not implemented yet. Use POST /analyze endpoint.');
  }

  async convert(_svgContent: string, _options: ConversionSettings): Promise<EngineResult> {
    throw new Error('LocalEngine.convert() not implemented yet. Use POST /convert endpoint.');
  }

  async exportGLB(_model: THREE.Group, _options: ExportOptions): Promise<Blob> {
    throw new Error('LocalEngine.exportGLB() not implemented yet.');
  }
}
