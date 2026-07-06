import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { ViewerScene } from './ViewerScene';
import { ImageOverlay } from './ImageOverlay';
import { LoadingFallback } from './LoadingFallback';

export function Viewer3D() {
  return (
    <div className="flex-1 relative bg-bg-primary">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        gl={{ antialias: true, alpha: false }}
      >
        <Suspense fallback={<LoadingFallback />}>
          <ViewerScene />
        </Suspense>
      </Canvas>

      <ImageOverlay />

      <div className="absolute bottom-4 left-4 flex items-center gap-2">
        <span className="px-2 py-1 text-[10px] font-mono text-text-muted bg-bg-secondary/80 backdrop-blur-sm rounded border border-border-primary">
          3D Viewport
        </span>
      </div>
    </div>
  );
}
