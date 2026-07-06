import { useModelStore } from '@/store/modelStore';

export function ImageOverlay() {
  const { fileType, fileUrl, svgContent, fileName, generatedModel } = useModelStore();

  if (!fileUrl) return null;
  if (generatedModel) return null;

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="relative max-w-[80%] max-h-[80%] rounded-lg overflow-hidden shadow-2xl border border-border-primary/50 bg-bg-secondary/80 backdrop-blur-sm">
        {fileType === 'png' && (
          <img
            src={fileUrl}
            alt={fileName}
            className="max-w-[500px] max-h-[500px] object-contain"
          />
        )}
        {fileType === 'svg' && svgContent && (
          <div
            className="w-full h-full flex items-center justify-center p-4 [&>svg]:max-w-[500px] [&>svg]:max-h-[500px]"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}
      </div>
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2">
        <span className="px-2 py-1 text-[10px] font-mono text-text-muted bg-bg-secondary/90 backdrop-blur-sm rounded border border-border-primary">
          {fileName} &middot; Preview
        </span>
      </div>
    </div>
  );
}
