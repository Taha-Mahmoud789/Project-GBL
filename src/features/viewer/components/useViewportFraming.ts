import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useModelStore } from '@/store/modelStore';

/**
 * Auto-frame camera to fit the current model in viewport.
 * Updates both camera position and OrbitControls target.
 */
export function useViewportFraming(controlsRef?: React.RefObject<OrbitControlsImpl | null>) {
  const { camera } = useThree();
  const generatedModel = useModelStore((s) => s.generatedModel);

  useEffect(() => {
    if (!generatedModel) return;

    generatedModel.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(generatedModel);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z);
    if (maxDim === 0) return;

    const fov = 50;
    const distance = (maxDim / 2) / Math.tan((fov / 2) * Math.PI / 180);
    const cameraZ = distance * 1.5;

    camera.position.set(center.x, center.y, center.z + cameraZ);
    (camera as THREE.PerspectiveCamera).near = 0.01;
    (camera as THREE.PerspectiveCamera).far = Math.max(100, cameraZ * 10);
    (camera as THREE.PerspectiveCamera).updateProjectionMatrix();
    camera.lookAt(center);

    if (controlsRef?.current) {
      controlsRef.current.target.copy(center);
      controlsRef.current.update();
    }
  }, [generatedModel, camera, controlsRef]);
}
