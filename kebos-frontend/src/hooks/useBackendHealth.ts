import { useState, useEffect, useCallback } from 'react';

type BackendHealthStatus = 'healthy' | 'unhealthy' | 'checking';

export function useBackendHealth(pollIntervalMs = 15000) {
  const [status, setStatus] = useState<BackendHealthStatus>('checking');

  const check = useCallback(async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const res = await fetch(`${apiUrl}/health`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      setStatus(res.ok ? 'healthy' : 'unhealthy');
    } catch {
      setStatus('unhealthy');
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, pollIntervalMs);
    return () => clearInterval(id);
  }, [check, pollIntervalMs]);

  return status;
}
