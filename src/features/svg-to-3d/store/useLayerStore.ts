import { create } from 'zustand';
import type * as THREE from 'three';
import type { LayerConfig, NormalizedShape } from '@/types';

function shapeToLayer(shape: NormalizedShape, index: number): LayerConfig {
  return {
    id: shape.id,
    name: shape.name,
    fillColor: shape.fillColor,
    opacity: shape.opacity,
    zIndex: shape.zIndex,
    depth: 0.5,
    bevelEnabled: true,
    bevelThickness: 0.03,
    bevelSize: 0.03,
    bevelSegments: 2,
    position: [0, 0, index * 0.02],
    rotation: [0, 0, 0],
    visible: true,
    shapeData: shape.shapeData as THREE.Shape,
  };
}

interface LayerStoreState {
  layers: LayerConfig[];
  globalDepth: number;
  globalBevelEnabled: boolean;
  globalBevelThickness: number;
  globalBevelSize: number;
  globalBevelSegments: number;
  setLayersFromShapes: (shapes: NormalizedShape[]) => void;
  updateLayer: (id: string, patch: Partial<LayerConfig>) => void;
  toggleVisibility: (id: string) => void;
  applyToAll: (patch: Partial<Pick<LayerConfig, 'depth' | 'bevelEnabled' | 'bevelThickness' | 'bevelSize' | 'bevelSegments'>>) => void;
  resetLayers: () => void;
}

export const useLayerStore = create<LayerStoreState>((set) => ({
  layers: [],
  globalDepth: 0.5,
  globalBevelEnabled: true,
  globalBevelThickness: 0.03,
  globalBevelSize: 0.03,
  globalBevelSegments: 2,

  setLayersFromShapes: (shapes) => {
    set({ layers: shapes.map((s, i) => shapeToLayer(s, i)) });
  },

  updateLayer: (id, patch) =>
    set((state) => ({
      layers: state.layers.map((l) => (l.id === id ? { ...l, ...patch } : l)),
    })),

  toggleVisibility: (id) =>
    set((state) => ({
      layers: state.layers.map((l) =>
        l.id === id ? { ...l, visible: !l.visible } : l,
      ),
    })),

  applyToAll: (patch) =>
    set((state) => ({
      layers: state.layers.map((l) => ({ ...l, ...patch })),
      ...('depth' in patch ? { globalDepth: patch.depth } : {}),
      ...('bevelEnabled' in patch ? { globalBevelEnabled: patch.bevelEnabled } : {}),
      ...('bevelThickness' in patch ? { globalBevelThickness: patch.bevelThickness } : {}),
      ...('bevelSize' in patch ? { globalBevelSize: patch.bevelSize } : {}),
      ...('bevelSegments' in patch ? { globalBevelSegments: patch.bevelSegments } : {}),
    })),

  resetLayers: () =>
    set((state) => ({
      layers: state.layers.map((l) => ({
        ...l,
        depth: 0.5,
        bevelEnabled: true,
        bevelThickness: 0.03,
        bevelSize: 0.03,
        bevelSegments: 2,
        position: [0, 0, l.zIndex * 0.02] as [number, number, number],
        rotation: [0, 0, 0] as [number, number, number],
        visible: true,
      })),
    })),
}));
