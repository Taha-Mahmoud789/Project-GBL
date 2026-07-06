export type ImageFormat = 'png' | 'svg';

export type ConversionMethod = 'depth' | 'extrusion' | 'neural';

export type ConversionMode = 'auto' | 'layered' | 'engraved';

export type ExportFormat = 'glb' | 'gltf' | 'obj';

export interface UploadedImage {
  id: string;
  file: File;
  name: string;
  format: ImageFormat;
  preview: string;
  width: number;
  height: number;
  uploadedAt: Date;
}

export interface ConversionSettings {
  method: ConversionMethod;
  mode: ConversionMode;
  depth: number;
  bevel: number;
  smoothness: number;
  scale: number;
  simplify: boolean;
  simplifyRatio: number;
  smoothNormals: boolean;
  invertY: boolean;
}

export interface MaterialSettings {
  metalness: number;
  roughness: number;
  color: string;
}

export interface ExportSettings {
  format: ExportFormat;
  includeMaterials: boolean;
  includeTextures: boolean;
}

export interface ViewportState {
  cameraPosition: [number, number, number];
  showGrid: boolean;
  showAxes: boolean;
  wireframe: boolean;
  backgroundColor: string;
}

export interface AppState {
  images: UploadedImage[];
  selectedImageId: string | null;
  conversionSettings: ConversionSettings;
  materialSettings: MaterialSettings;
  exportSettings: ExportSettings;
  viewport: ViewportState;
  isConverting: boolean;
  isExporting: boolean;

  addImage: (image: UploadedImage) => void;
  removeImage: (id: string) => void;
  selectImage: (id: string | null) => void;
  updateConversionSettings: (settings: Partial<ConversionSettings>) => void;
  updateMaterialSettings: (settings: Partial<MaterialSettings>) => void;
  updateExportSettings: (settings: Partial<ExportSettings>) => void;
  updateViewport: (state: Partial<ViewportState>) => void;
  setConverting: (value: boolean) => void;
  setExporting: (value: boolean) => void;
}

// ponytail: SVG-to-3D feature types

/** A normalized shape extracted from SVG, ready for 3D extrusion. */
export interface NormalizedShape {
  id: string;
  name: string;
  /** THREE.Shape data (2D outline with holes) */
  shapeData: unknown;
  fillColor: string;
  strokeColor: string;
  opacity: number;
  /** Original z-order (index) in the SVG file */
  zIndex: number;
}

/** Per-layer 3D configuration. */
export interface LayerConfig {
  id: string;
  name: string;
  fillColor: string;
  opacity: number;
  zIndex: number;
  /** Extrusion depth */
  depth: number;
  bevelEnabled: boolean;
  bevelThickness: number;
  bevelSize: number;
  bevelSegments: number;
  position: [number, number, number];
  rotation: [number, number, number];
  visible: boolean;
  /** 2D shape data for extrusion — lives in the store so renderers don't re-extract */
  shapeData: import('three').Shape;
}

/** GLB export options. */
export interface ExportOptions {
  /** Merge all layers into one mesh, or keep separate */
  mode: 'merged' | 'separate';
  filename: string;
}

/** Store state for the SVG-to-3D layer system. */
export interface LayerStoreState {
  layers: LayerConfig[];
  globalDepth: number;
  globalBevelEnabled: boolean;
  globalBevelThickness: number;
  globalBevelSize: number;
  globalBevelSegments: number;
  setLayers: (layers: LayerConfig[]) => void;
  updateLayer: (id: string, patch: Partial<LayerConfig>) => void;
  toggleVisibility: (id: string) => void;
  applyToAll: (patch: Partial<Pick<LayerConfig, 'depth' | 'bevelEnabled' | 'bevelThickness' | 'bevelSize' | 'bevelSegments'>>) => void;
  resetLayers: () => void;
}
