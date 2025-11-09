import { create } from 'zustand';

interface Message {
  id: string;
  content: string;
  username: string;
  user: any;
  created_at: string;
  is_edited: boolean;
  reactions?: any[];
  attachments?: any[];
}

interface ChatState {
  currentRoomSlug: string | null;
  messages: Message[];
  typingUsers: string[];
  onlineUsers: string[];
  setCurrentRoom: (slug: string) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  deleteMessage: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  addTypingUser: (username: string) => void;
  removeTypingUser: (username: string) => void;
  setOnlineUsers: (users: string[]) => void;
  clearRoom: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentRoomSlug: null,
  messages: [],
  typingUsers: [],
  onlineUsers: [],

  setCurrentRoom: (slug: string) => set({ currentRoomSlug: slug, messages: [] }),

  addMessage: (message: Message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  updateMessage: (id: string, updates: Partial<Message>) => set((state) => ({
    messages: state.messages.map((msg) =>
      msg.id === id ? { ...msg, ...updates } : msg
    ),
  })),

  deleteMessage: (id: string) => set((state) => ({
    messages: state.messages.filter((msg) => msg.id !== id),
  })),

  setMessages: (messages: Message[]) => set({ messages }),

  addTypingUser: (username: string) => set((state) => ({
    typingUsers: state.typingUsers.includes(username)
      ? state.typingUsers
      : [...state.typingUsers, username],
  })),

  removeTypingUser: (username: string) => set((state) => ({
    typingUsers: state.typingUsers.filter((u) => u !== username),
  })),

  setOnlineUsers: (users: string[]) => set({ onlineUsers: users }),

  clearRoom: () => set({
    currentRoomSlug: null,
    messages: [],
    typingUsers: [],
    onlineUsers: [],
  }),
}));
