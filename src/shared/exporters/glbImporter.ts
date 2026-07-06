import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

/**
 * Parse GLB bytes (ArrayBuffer) into a THREE.Group.
 * Used to load server-generated GLB for preview in the R3F viewer.
 */
export async function parseGlbBytes(buffer: ArrayBuffer): Promise<THREE.Group> {
  const loader = new GLTFLoader();

  return new Promise((resolve, reject) => {
    loader.parse(
      buffer,
      '',
      (gltf) => {
        const group = new THREE.Group();
        group.name = 'Imported GLB';

        gltf.scene.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            // Clone mesh so it's independent of the GLTF scene
            const cloned = child.clone();
            cloned.name = child.name || `Layer ${group.children.length + 1}`;
            // Apply world transform to mesh
            child.getWorldPosition(cloned.position);
            child.getWorldQuaternion(cloned.quaternion);
            child.getWorldScale(cloned.scale);
            group.add(cloned);
          }
        });

        // If no meshes found, add the whole scene
        if (group.children.length === 0) {
          group.add(gltf.scene.clone());
        }

        resolve(group);
      },
      (error) => reject(error),
    );
  });
}
