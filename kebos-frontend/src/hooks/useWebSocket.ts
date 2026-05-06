import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/authStore';

type ConnectionStatus = 'connected' | 'polling' | 'disconnected';

interface UseWebSocketOptions {
  url: string;
  enabled: boolean;
  onMessage?: (data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket({
  url,
  enabled,
  onMessage,
  onConnect,
  onDisconnect,
}: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;
  const baseReconnectDelay = 5000;
  useAuthStore();

  const connect = () => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) return;

    // Cookie is sent automatically by the browser with the WebSocket upgrade request.
    // Backend reads auth from the HttpOnly access_token cookie.
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onclose = () => {
        setStatus('disconnected');
        onDisconnect?.();
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('polling');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          onMessage?.(event.data);
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setStatus('disconnected');

      // Attempt reconnect
      reconnectAttemptsRef.current++;
      if (reconnectAttemptsRef.current <= maxReconnectAttempts) {
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, baseReconnectDelay);
      }
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
  };

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, url]);

  return { status, connect, disconnect };
}
