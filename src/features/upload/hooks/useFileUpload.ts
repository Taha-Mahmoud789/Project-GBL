import { useCallback } from 'react';
import { useModelStore } from '@/store/modelStore';
import { ACCEPTED_TYPES, ACCEPTED_EXTENSIONS } from '@/shared/constants';

function validateFile(file: File): string | null {
  if (file.type in ACCEPTED_TYPES) return null;

  const name = file.name.toLowerCase();
  const hasValidExt = ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
  if (hasValidExt) return null;

  return `"${file.name}" is not supported. Only PNG and SVG files are accepted.`;
}

function readSvgContent(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = () => reject(new Error('Failed to read SVG file'));
    reader.readAsText(file);
  });
}

function readPngPreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = () => reject(new Error('Failed to read PNG file'));
    reader.readAsDataURL(file);
  });
}

export function useFileUpload() {
  const { setUploadedFile, setError, setLoading, clearFile } = useModelStore();

  const processFile = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

      setLoading(true);

      try {
        const isSvg = file.type === 'image/svg+xml';

        if (isSvg) {
          const url = URL.createObjectURL(file);
          const svgContent = await readSvgContent(file);
          setUploadedFile(file, url, svgContent);
        } else {
          const url = await readPngPreview(file);
          setUploadedFile(file, url, null);
        }
      } catch {
        setError('Failed to process the file. Please try again.');
      }
    },
    [setUploadedFile, setError, setLoading],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      processFile(files[0]);
    },
    [processFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  return {
    handleFiles,
    handleDrop,
    handleDragOver,
    clearFile,
  };
}
