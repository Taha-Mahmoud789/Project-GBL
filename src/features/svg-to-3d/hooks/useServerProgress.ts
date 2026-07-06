import { useState, useCallback, useRef } from 'react';

interface ProgressState {
  progress: number;
  message: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
}

/**
 * Hook to consume SSE progress from the FastAPI server.
 * Usage: call startPolling(taskId) after initiating a conversion.
 */
export function useServerProgress(baseUrl = 'http://localhost:8000') {
  const [progress, setProgress] = useState<ProgressState>({
    progress: 0,
    message: '',
    status: 'idle',
  });
  const abortRef = useRef<AbortController | null>(null);

  const startPolling = useCallback(
    (taskId: string) => {
      // Cancel any existing poll
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setProgress({ progress: 0, message: 'Starting...', status: 'running' });

      const url = `${baseUrl}/progress/${taskId}/stream`;
      fetch(url, { signal: controller.signal })
        .then(async (res) => {
          if (!res.ok || !res.body) {
            setProgress((p) => ({ ...p, status: 'failed', message: `HTTP ${res.status}` }));
            return;
          }

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              try {
                const data = JSON.parse(line.slice(6));
                setProgress({
                  progress: data.progress,
                  message: data.message,
                  status: data.status,
                });
                if (data.status === 'completed' || data.status === 'failed') return;
              } catch {
                // skip malformed
              }
            }
          }
        })
        .catch((err) => {
          if (err.name !== 'AbortError') {
            setProgress((p) => ({ ...p, status: 'failed', message: String(err) }));
          }
        });
    },
    [baseUrl],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setProgress({ progress: 0, message: '', status: 'idle' });
  }, []);

  return { progress, startPolling, stop };
}
