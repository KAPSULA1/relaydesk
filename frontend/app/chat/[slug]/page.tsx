'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, Users, Smile, Paperclip, MoreVertical } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chatStore';
import { useUIStore } from '@/lib/stores/uiStore';
import { MessageSkeleton } from '@/components/ui/Skeleton';
import { ToastContainer } from '@/components/ui/Toast';
import api from '@/lib/api/axios-client';
import { resolveWebSocketBase } from '@/lib/config';

interface Room {
  id: string;
  name: string;
  slug: string;
}

interface User {
  id: number;
  username: string;
  email: string;
}

export default function ChatPage() {
  const params = useParams();
  const slugParam = params?.slug;
  const roomSlug = useMemo(() => {
    if (Array.isArray(slugParam)) return slugParam[0] ?? '';
    if (typeof slugParam === 'string') return slugParam;
    return '';
  }, [slugParam]);

  const [room, setRoom] = useState<Room | null>(null);
  const [roomError, setRoomError] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [connectionState, setConnectionState] = useState<'idle' | 'connecting' | 'connected' | 'reconnecting' | 'disconnected'>('idle');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [authToken, setAuthToken] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const manualCloseRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, setMessages, addMessage, typingUsers } = useChatStore();
  const { theme, addNotification } = useUIStore();

  useEffect(() => {
    console.log('[ChatPage Mount]', { roomSlug });
  }, [roomSlug]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const token = window.localStorage.getItem('access_token');
    if (!token) {
      window.location.assign('/login');
      return;
    }
    setAuthToken(token);
  }, []);

  useEffect(() => {
    if (!roomSlug) {
      setRoomError('Room slug missing from URL.');
      setLoading(false);
      return;
    }
    if (!authToken) return;

    console.log('[ChatPage] loading room data', { roomSlug });
    let cancelled = false;
    setLoading(true);

    const bootstrap = async () => {
      try {
        const [userRes, roomRes, messagesRes] = await Promise.all([
          api.get<User>('/api/auth/me/'),
          api.get<Room>(`/api/rooms/${roomSlug}/`),
          api.get(`/api/rooms/${roomSlug}/messages/`),
        ]);

        if (cancelled) return;
        setCurrentUser(userRes.data);
        setRoom(roomRes.data);
        setRoomError(null);
        setMessages(Array.isArray(messagesRes.data) ? messagesRes.data : []);
      } catch (error) {
        if (cancelled) return;
        console.error('Failed to bootstrap chat:', error);
        addNotification({ type: 'error', message: 'Failed to load chat data.' });
        setRoomError('We could not load this room. Please try again.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [roomSlug, authToken, addNotification, setMessages]);

  useEffect(() => {
    if (!roomSlug || !authToken) return;

    console.log('[WS Init]', { roomSlug });
    const wsUrl = `${resolveWebSocketBase()}/ws/chat/${roomSlug}/?token=${encodeURIComponent(authToken)}`;

    const connectSocket = () => {
      console.log('Attempting WS', { roomSlug });
      manualCloseRef.current = false;
      setConnectionState((prev) => (prev === 'connected' ? 'connected' : 'connecting'));

      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      const socket = new WebSocket(wsUrl);
      ws.current = socket;

      socket.onopen = () => {
        console.log('WS connected');
        setConnectionState('connected');
        socket.send(JSON.stringify({ type: 'join', message: 'Client joined the room' }));
        pingIntervalRef.current = setInterval(() => {
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
            console.log('WS ping sent');
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        console.log('WS message', event.data);
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'chat_message' && payload.message) {
            addMessage(payload.message);
          } else if (payload.type === 'error') {
            addNotification({ type: 'error', message: payload.message || 'An error occurred' });
          }
        } catch (error) {
          console.error('Failed to parse WebSocket payload:', error);
        }
      };

      socket.onerror = (error) => {
        if (manualCloseRef.current) return;
        console.error('WebSocket error:', error);
        addNotification({ type: 'error', message: 'Connection error' });
      };

      socket.onclose = (event) => {
        if (manualCloseRef.current) return;
        console.warn('WS disconnected', event.code, event.reason);
        setConnectionState('disconnected');
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        reconnectTimerRef.current = window.setTimeout(() => {
          console.log('WS reconnecting');
          setConnectionState('reconnecting');
          connectSocket();
        }, 2000);
      };
    };

    connectSocket();
    return () => {
      if (ws.current) {
        manualCloseRef.current = true;
        ws.current.close();
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      setConnectionState('idle');
    };
  }, [roomSlug, authToken, addMessage, addNotification]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const isConnected = connectionState === 'connected';
  const connectionLabel = useMemo(() => {
    switch (connectionState) {
      case 'connected':
        return { text: 'Connected', dotClass: 'bg-emerald-400', textClass: 'text-emerald-400' };
      case 'reconnecting':
        return { text: 'Reconnecting…', dotClass: 'bg-amber-400 animate-pulse', textClass: 'text-amber-300' };
      case 'disconnected':
        return { text: 'Disconnected', dotClass: 'bg-red-500 animate-pulse', textClass: 'text-red-400' };
      default:
        return { text: 'Connecting…', dotClass: 'bg-amber-400 animate-pulse', textClass: 'text-amber-300' };
    }
  }, [connectionState]);

  const roomTitle = room?.name || roomSlug || 'Chat';

  const sendMessage = () => {
    if (!isConnected || !message.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    ws.current.send(JSON.stringify({ type: 'chat_message', message: message.trim() }));
    setMessage('');
  };

  const goBack = () => window.location.assign('/rooms');

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-[#0a0a0b]' : 'bg-gray-50'}`}>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4 max-w-2xl w-full px-4">
          {[...Array(5)].map((_, i) => (
            <MessageSkeleton key={i} />
          ))}
        </motion.div>
      </div>
    );
  }

  if (!room && roomError) {
    return (
      <div className={`min-h-screen flex flex-col items-center justify-center gap-6 px-4 ${theme === 'dark' ? 'bg-[#0a0a0b] text-gray-300' : 'bg-gray-50 text-gray-700'}`}>
        <ToastContainer />
        <div className="max-w-md text-center space-y-4">
          <h2 className="text-2xl font-semibold">{roomError}</h2>
          <p className="text-sm">Try refreshing the page or navigating back to rooms.</p>
        </div>
        <button onClick={goBack} className="px-5 py-3 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white font-medium shadow-lg shadow-purple-500/30 hover:shadow-purple-500/60 transition-all">
          Back to rooms
        </button>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col ${theme === 'dark' ? 'bg-[#0a0a0b]' : 'bg-gray-50'}`}>
      <ToastContainer />
      <header className={`border-b ${theme === 'dark' ? 'border-white/5 bg-[#111113]/95' : 'border-gray-200 bg-white/95'} backdrop-blur-xl sticky top-0 z-50 shadow-sm`}>
        <div className="px-4 py-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <motion.button whileHover={{ scale: 1.1, rotate: -90 }} whileTap={{ scale: 0.9 }} onClick={goBack} className={`p-1.5 rounded-lg transition-colors ${theme === 'dark' ? 'text-gray-400 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}`}>
                <ArrowLeft className="w-5 h-5" />
              </motion.button>
              <div className="flex items-center gap-3">
                <motion.div initial={{ scale: 0, rotate: -180 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: 'spring', stiffness: 200 }} className="w-10 h-10 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30 ring-2 ring-purple-500/20">
                  <span className="text-white font-bold text-lg">{roomTitle[0]?.toUpperCase()}</span>
                </motion.div>
                <div>
                  <h1 className={`text-lg font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>{roomTitle}</h1>
                  <motion.p initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className={`text-xs flex items-center gap-1.5 ${connectionLabel.textClass}`}>
                    <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }} className={`w-2 h-2 rounded-full ${connectionLabel.dotClass}`} />
                    <span className="font-medium">{connectionLabel.text}</span>
                  </motion.p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <motion.button whileHover={{ scale: 1.05, rotate: 5 }} whileTap={{ scale: 0.95 }} className={`p-2 rounded-lg transition-all ${theme === 'dark' ? 'hover:bg-white/5 text-gray-400 hover:text-white' : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
                <Users className="w-5 h-5" />
              </motion.button>
              <motion.button whileHover={{ scale: 1.05, rotate: 90 }} whileTap={{ scale: 0.95 }} className={`p-2 rounded-lg transition-all ${theme === 'dark' ? 'hover:bg-white/5 text-gray-400 hover:text-white' : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
                <MoreVertical className="w-5 h-5" />
              </motion.button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-hide">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 ? (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center justify-center h-full">
              <div className={`text-center ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                <p className="text-lg mb-2">No messages yet</p>
                <p className="text-sm">Be the first to say something!</p>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((msg, index) => {
                const isCurrentUser = currentUser && msg.user && msg.user.id === currentUser.id;
                return (
                  <motion.div key={msg.id || index} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9 }} transition={{ duration: 0.2 }} className={`flex ${isCurrentUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`flex gap-3 max-w-lg ${isCurrentUser ? 'flex-row-reverse' : ''}`}>
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 500, damping: 20 }} className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 ring-2 ${isCurrentUser ? 'bg-gradient-to-br from-blue-500 to-indigo-600 ring-blue-500/30' : 'bg-gradient-to-br from-purple-500 to-pink-600 ring-purple-500/30'}`}>
                        {(msg.username || 'U')[0].toUpperCase()}
                      </motion.div>
                      <div className="flex flex-col gap-1">
                        <motion.div initial={{ opacity: 0, x: isCurrentUser ? 10 : -10 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2">
                          <span className={`text-xs font-semibold ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                            {msg.username || 'Unknown'}
                          </span>
                          <span className={`text-[10px] ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>
                            {new Date(msg.created_at).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </motion.div>
                        <motion.div whileHover={{ scale: 1.01, y: -1 }} transition={{ type: 'spring', stiffness: 400 }} className={`px-4 py-2.5 rounded-2xl shadow-sm ${isCurrentUser ? 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white rounded-tr-md shadow-purple-500/20' : theme === 'dark' ? 'bg-[#1a1a1c] text-gray-100 rounded-tl-md border border-white/5' : 'bg-white text-gray-900 rounded-tl-md border border-gray-200'}`}>
                          <p className="text-sm break-words whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </motion.div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {typingUsers.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }} className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} italic px-4`}>
              {typingUsers[0]} is typing...
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className={`border-t ${theme === 'dark' ? 'border-white/5 bg-[#111113]/95' : 'border-gray-200 bg-white/95'} backdrop-blur-xl p-4 shadow-lg`}>
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2.5 items-end">
            <motion.button whileHover={{ scale: 1.1, rotate: 15 }} whileTap={{ scale: 0.9 }} className={`p-2.5 rounded-xl transition-all ${theme === 'dark' ? 'hover:bg-white/5 text-gray-400 hover:text-purple-400' : 'hover:bg-gray-100 text-gray-600 hover:text-purple-600'}`}>
              <Paperclip className="w-5 h-5" />
            </motion.button>
            <div className="flex-1 relative">
              <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()} placeholder={isConnected ? 'Type a message...' : 'Waiting for connection...'} disabled={!isConnected} className={`w-full px-4 py-3 rounded-xl border transition-all ${theme === 'dark' ? 'bg-[#1a1a1c] border-white/10 text-white placeholder-gray-500 focus:border-purple-500/50 disabled:bg-[#0f0f10] disabled:cursor-not-allowed' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-purple-500/50 disabled:bg-gray-100 disabled:cursor-not-allowed'} focus:outline-none focus:ring-2 focus:ring-purple-500/20`} />
            </div>
            <motion.button whileHover={{ scale: 1.1, rotate: 15 }} whileTap={{ scale: 0.9 }} className={`p-2.5 rounded-xl transition-all ${theme === 'dark' ? 'hover:bg-white/5 text-gray-400 hover:text-yellow-400' : 'hover:bg-gray-100 text-gray-600 hover:text-yellow-600'}`}>
              <Smile className="w-5 h-5" />
            </motion.button>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={sendMessage} disabled={!isConnected || !message.trim()} className="px-5 py-3 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all flex items-center justify-center shadow-lg shadow-purple-500/30 disabled:shadow-none">
              <Send className="w-5 h-5" />
            </motion.button>
          </div>
          {connectionState !== 'connected' && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs text-yellow-400 mt-2 flex items-center gap-2">
              <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
              {connectionState === 'connecting' ? 'Connecting to chat…' : 'Reconnecting to chat…'}
            </motion.p>
          )}
        </div>
      </div>
    </div>
  );
}
