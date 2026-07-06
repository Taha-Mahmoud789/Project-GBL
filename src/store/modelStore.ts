import { create } from 'zustand';
import type * as THREE from 'three';
import type { ConversionMode } from '@/types';

type FileType = 'png' | 'svg' | null;

interface ModelSettings {
  depth: number;
  bevel: number;
  smoothness: number;
  mode: ConversionMode;
  material: { color: string; metalness: number; roughness: number };
}

interface SVGAnalysisResult {
  type: string;
  stats: { paths: number; fills: number; strokes: number; images: number; texts: number; masks: number; filters: number };
  recommendedEngine: string;
  warnings: string[];
}

interface VectorizationInfo {
  detected: boolean;
  pathCount: number;
  timing: number;
  originalType: string;
}

interface ModelFileState {
  uploadedFile: File | null;
  fileName: string;
  fileType: FileType;
  fileUrl: string | null;
  svgContent: string | null;
  isLoading: boolean;
  error: string | null;

  modelSettings: ModelSettings;
  generatedModel: THREE.Group | null;
  svgAnalysis: SVGAnalysisResult | null;
  vectorizationInfo: VectorizationInfo | null;

  setUploadedFile: (file: File, url: string, svgContent: string | null) => void;
  clearFile: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  updateModelSettings: (settings: Partial<ModelSettings>) => void;
  setGeneratedModel: (model: THREE.Group | null) => void;
  setSvgAnalysis: (analysis: SVGAnalysisResult | null) => void;
  setVectorizationInfo: (info: VectorizationInfo | null) => void;
}

export const useModelStore = create<ModelFileState>((set, get) => ({
  uploadedFile: null,
  fileName: '',
  fileType: null,
  fileUrl: null,
  svgContent: null,
  isLoading: false,
  error: null,

  modelSettings: {
    depth: 0.5,
    bevel: 0.05,
    smoothness: 5,
    mode: 'auto' as ConversionMode,
    material: { color: '#6366f1', metalness: 0.2, roughness: 0.3 },
  },
  generatedModel: null,
  svgAnalysis: null,
  vectorizationInfo: null,

  setUploadedFile: (file, url, svgContent) => {
    const prev = get().fileUrl;
    if (prev) URL.revokeObjectURL(prev);

    set({
      uploadedFile: file,
      fileName: file.name,
      fileType: file.type === 'image/svg+xml' ? 'svg' : 'png',
      fileUrl: url,
      svgContent,
      isLoading: false,
      error: null,
    });
  },

  clearFile: () => {
    const prev = get().fileUrl;
    if (prev) URL.revokeObjectURL(prev);

    set({
      uploadedFile: null,
      fileName: '',
      fileType: null,
      fileUrl: null,
      svgContent: null,
      isLoading: false,
      error: null,
      generatedModel: null,
    });
  },

  setError: (error) => set({ error, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),

  updateModelSettings: (settings) =>
    set((state) => ({
      modelSettings: { ...state.modelSettings, ...settings },
    })),

  setGeneratedModel: (model) => set({ generatedModel: model }),
  setSvgAnalysis: (analysis) => set({ svgAnalysis: analysis }),
  setVectorizationInfo: (info) => set({ vectorizationInfo: info }),
}));
