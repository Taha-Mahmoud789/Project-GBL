import { useModelStore } from '@/store/modelStore';

export function ModelRenderer() {
  const generatedModel = useModelStore((s) => s.generatedModel);

  if (!generatedModel) return null;

  return <primitive object={generatedModel} />;
}
