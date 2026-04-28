import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

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
  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000;

  const connect = () => {
    if (!enabled || socketRef.current?.connected) return;

    const socket = io(url, {
      reconnection: true,
      reconnectionDelay: baseReconnectDelay,
      reconnectionAttempts: maxReconnectAttempts,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setStatus('connected');
      reconnectAttemptsRef.current = 0;
      onConnect?.();
    });

    socket.on('disconnect', () => {
      setStatus('disconnected');
      onDisconnect?.();
    });

    socket.on('connect_error', () => {
      setStatus('polling');
      reconnectAttemptsRef.current++;
      
      // Exponential backoff
      const delay = Math.min(
        baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current),
        30000
      );

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          connect();
        }
      }, delay);
    });

    if (onMessage) {
      socket.on('message', onMessage);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    socketRef.current?.disconnect();
    socketRef.current = null;
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
