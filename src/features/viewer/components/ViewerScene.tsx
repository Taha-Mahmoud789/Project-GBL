import { useRef } from 'react';
import { OrbitControls, Grid, GizmoHelper, GizmoViewport } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useAppStore } from '@/store';
import { ModelRenderer } from './ModelRenderer';
import { useViewportFraming } from './useViewportFraming';

export function ViewerScene() {
  const { viewport } = useAppStore();
  const controlsRef = useRef<OrbitControlsImpl>(null);
  useViewportFraming(controlsRef);

  const isDark = parseInt(viewport.backgroundColor.replace('#', ''), 16) < 0x808080;
  const cellColor = isDark ? '#2a2a3a' : '#c0c0c0';
  const sectionColor = isDark ? '#3a3a4a' : '#a0a0a0';

  return (
    <>
      <color attach="background" args={[viewport.backgroundColor]} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} />
      <directionalLight position={[-5, 3, -5]} intensity={0.3} />

      <ModelRenderer />

      {viewport.showGrid && (
        <Grid
          args={[20, 20]}
          cellSize={0.5}
          cellThickness={0.5}
          cellColor={cellColor}
          sectionSize={2}
          sectionThickness={1}
          sectionColor={sectionColor}
          fadeDistance={25}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid
        />
      )}

      {viewport.showAxes && (
        <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
          <GizmoViewport />
        </GizmoHelper>
      )}

      <OrbitControls
        ref={controlsRef}
        makeDefault
        enableDamping
        dampingFactor={0.1}
        minDistance={1}
        maxDistance={50}
      />
    </>
  );
}
