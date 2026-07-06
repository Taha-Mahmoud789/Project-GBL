import { useCallback, useRef, useState } from 'react';
import { Upload, X, FileImage, AlertCircle, Loader2 } from 'lucide-react';
import { useModelStore } from '@/store/modelStore';
import { useFileUpload } from '../hooks/useFileUpload';

export function UploadPanel() {
  const { uploadedFile, fileName, fileType, fileUrl, svgContent, isLoading, error } =
    useModelStore();
  const { handleFiles, handleDrop, handleDragOver, clearFile } = useFileUpload();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const onDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) setIsDragging(false);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      setIsDragging(false);
      handleDrop(e);
    },
    [handleDrop],
  );

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      e.target.value = '';
    },
    [handleFiles],
  );

  return (
    <div className="flex flex-col h-full">
      {/* Drop Zone / File Info */}
      <div className="px-3 pt-3">
        {!uploadedFile && !isLoading && !error && (
          <div
            onDrop={onDrop}
            onDragOver={handleDragOver}
            onDragEnter={onDragEnter}
            onDragLeave={onDragLeave}
            onClick={() => inputRef.current?.click()}
            className={`flex flex-col items-center justify-center gap-3 p-6 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
              isDragging
                ? 'border-accent bg-accent/10 scale-[1.02]'
                : 'border-border-secondary hover:border-accent/50 hover:bg-accent/5'
            }`}
          >
            <Upload className="w-8 h-8 text-text-muted" />
            <div className="text-center">
              <p className="text-sm font-medium text-text-secondary">
                Drop PNG or SVG
              </p>
              <p className="text-xs text-text-muted mt-1">
                or click to browse
              </p>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-bg-tertiary text-text-muted border border-border-primary">
                .PNG
              </span>
              <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-bg-tertiary text-text-muted border border-border-primary">
                .SVG
              </span>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-3 p-6 border-2 border-dashed border-accent/30 rounded-xl bg-accent/5">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
            <p className="text-sm font-medium text-text-secondary">Processing file...</p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center gap-3 p-6 border-2 border-dashed border-danger/30 rounded-xl bg-danger/5">
            <AlertCircle className="w-8 h-8 text-danger" />
            <div className="text-center">
              <p className="text-sm font-medium text-danger">Upload Error</p>
              <p className="text-xs text-text-muted mt-1">{error}</p>
            </div>
            <button
              onClick={clearFile}
              className="px-3 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary bg-bg-tertiary hover:bg-bg-secondary rounded-md border border-border-primary transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        {uploadedFile && !isLoading && (
          <div className="flex flex-col gap-3 p-3 border border-border-primary rounded-xl bg-bg-secondary">
            <div className="flex items-start gap-3">
              <div className="relative w-12 h-12 rounded-lg overflow-hidden bg-bg-tertiary shrink-0 border border-border-primary">
                {fileType === 'png' && fileUrl && (
                  <img src={fileUrl} alt={fileName} className="w-full h-full object-cover" />
                )}
                {fileType === 'svg' && svgContent && (
                  <div
                    className="w-full h-full flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                    dangerouslySetInnerHTML={{ __html: svgContent }}
                  />
                )}
                {fileType === 'svg' && !svgContent && fileUrl && (
                  <img src={fileUrl} alt={fileName} className="w-full h-full object-cover" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-text-primary truncate">{fileName}</p>
                <p className="text-[10px] text-text-muted mt-0.5">
                  {fileType?.toUpperCase()} &middot; {(uploadedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={clearFile}
                className="p-1.5 hover:bg-danger/15 rounded-md transition-colors group shrink-0"
              >
                <X className="w-3.5 h-3.5 text-text-muted group-hover:text-danger" />
              </button>
            </div>

            <div className="flex gap-2">
              <label className="flex-1 flex items-center justify-center px-3 py-2 text-xs font-medium text-text-secondary hover:text-text-primary bg-bg-tertiary hover:bg-bg-secondary rounded-lg border border-border-primary cursor-pointer transition-colors">
                Replace
                <input
                  ref={inputRef}
                  type="file"
                  accept=".png,.svg,image/png,image/svg+xml"
                  onChange={onInputChange}
                  className="hidden"
                />
              </label>
              <button
                onClick={clearFile}
                className="px-3 py-2 text-xs font-medium text-danger hover:text-danger/80 bg-danger/10 hover:bg-danger/15 rounded-lg border border-danger/20 transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Hidden file input for empty state */}
      {!uploadedFile && !isLoading && (
        <input
          ref={inputRef}
          type="file"
          accept=".png,.svg,image/png,image/svg+xml"
          onChange={onInputChange}
          className="hidden"
        />
      )}

      {/* File list / empty state */}
      {!uploadedFile && !isLoading && !error && (
        <div className="flex-1 flex flex-col items-center justify-center px-3 pb-3">
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <FileImage className="w-10 h-10 text-text-muted/30 mb-3" />
            <p className="text-xs text-text-muted">No file uploaded</p>
            <p className="text-[10px] text-text-muted/60 mt-1">
              Supports PNG and SVG formats
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
