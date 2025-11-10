import { useEffect, useRef, useState } from 'react';
import { WS_HOST } from '../config';

export function useWebSocket(roomSlug: string, token: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!token || !roomSlug || typeof window === 'undefined') return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const baseUrl = `${protocol}://${WS_HOST}`;
    const wsUrl = `${baseUrl}/ws/chat/${roomSlug}/?token=${encodeURIComponent(token)}`;

    const connect = () => {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        reconnectAttempts.current = 0;
        setIsConnected(true);
      };

      ws.current.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setMessages((prev) => [...prev, data]);
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        const attempt = reconnectAttempts.current + 1;
        reconnectAttempts.current = attempt;
        const delay = Math.min(5000, attempt * 1000);
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
    };
  }, [roomSlug, token]);

  const sendMessage = (message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'chat_message', message }));
    }
  };

  return { isConnected, messages, sendMessage };
}
