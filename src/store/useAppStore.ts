import { create } from 'zustand';
import type { AppState, ConversionSettings, MaterialSettings, ExportSettings, ViewportState, UploadedImage } from '@/types';

const defaultConversionSettings: ConversionSettings = {
  method: 'depth',
  mode: 'auto',
  depth: 1.0,
  bevel: 0.2,
  smoothness: 0.5,
  scale: 1.0,
  simplify: false,
  simplifyRatio: 0.5,
  smoothNormals: true,
  invertY: false,
};

const defaultMaterialSettings: MaterialSettings = {
  metalness: 0.0,
  roughness: 0.7,
  color: '#6366f1',
};

const defaultExportSettings: ExportSettings = {
  format: 'glb',
  includeMaterials: true,
  includeTextures: true,
};

const defaultViewport: ViewportState = {
  cameraPosition: [3, 2, 5],
  showGrid: true,
  showAxes: true,
  wireframe: false,
  backgroundColor: '#111111',
};

export const useAppStore = create<AppState>((set) => ({
  images: [],
  selectedImageId: null,
  conversionSettings: defaultConversionSettings,
  materialSettings: defaultMaterialSettings,
  exportSettings: defaultExportSettings,
  viewport: defaultViewport,
  isConverting: false,
  isExporting: false,

  addImage: (image: UploadedImage) =>
    set((state: AppState) => ({
      images: [...state.images, image],
      selectedImageId: image.id,
    })),

  removeImage: (id: string) =>
    set((state: AppState) => ({
      images: state.images.filter((img: UploadedImage) => img.id !== id),
      selectedImageId:
        state.selectedImageId === id
          ? state.images.filter((img: UploadedImage) => img.id !== id)[0]?.id ?? null
          : state.selectedImageId,
    })),

  selectImage: (id: string | null) =>
    set({ selectedImageId: id }),

  updateConversionSettings: (settings: Partial<ConversionSettings>) =>
    set((state: AppState) => ({
      conversionSettings: { ...state.conversionSettings, ...settings },
    })),

  updateMaterialSettings: (settings: Partial<MaterialSettings>) =>
    set((state: AppState) => ({
      materialSettings: { ...state.materialSettings, ...settings },
    })),

  updateExportSettings: (settings: Partial<ExportSettings>) =>
    set((state: AppState) => ({
      exportSettings: { ...state.exportSettings, ...settings },
    })),

  updateViewport: (viewportState: Partial<ViewportState>) =>
    set((state: AppState) => ({
      viewport: { ...state.viewport, ...viewportState },
    })),

  setConverting: (value: boolean) =>
    set({ isConverting: value }),

  setExporting: (value: boolean) =>
    set({ isExporting: value }),
}));
