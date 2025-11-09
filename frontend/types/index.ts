export interface User {
  id: number;
  username: string;
  email: string;
  date_joined: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Room {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  created_by: User;
  created_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  room: string;
  user: User;
  username: string;
  content: string;
  created_at: string;
  is_edited: boolean;
}

export interface WSMessage {
  type: 'chat_message' | 'user_joined' | 'user_left' | 'typing_indicator';
  message?: Message;
  username?: string;
  user_id?: number;
  is_typing?: boolean;
  online_users?: OnlineUser[];
}

export interface OnlineUser {
  id: number;
  username: string;
}
