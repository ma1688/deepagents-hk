import { create } from 'zustand';
import { Message, Conversation, ConversationListItem } from '@/types';

interface ChatState {
  // Current conversation
  currentConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  
  // Conversations list
  conversations: ConversationListItem[];
  
  // WebSocket
  ws: WebSocket | null;
  
  // Actions
  setCurrentConversation: (id: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setIsStreaming: (streaming: boolean) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
  setConversations: (conversations: ConversationListItem[]) => void;
  addConversation: (conversation: ConversationListItem) => void;
  removeConversation: (id: string) => void;
  updateConversationTitle: (id: string, title: string) => void;
  setWebSocket: (ws: WebSocket | null) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  conversations: [],
  ws: null,
  
  setCurrentConversation: (id) => set({ currentConversationId: id }),
  
  setMessages: (messages) => set({ messages }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),
  
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  
  setStreamingContent: (content) => set({ streamingContent: content }),
  
  appendStreamingContent: (content) => set((state) => ({
    streamingContent: state.streamingContent + content,
  })),
  
  clearStreamingContent: () => set({ streamingContent: '' }),
  
  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations],
  })),
  
  removeConversation: (id) => set((state) => ({
    conversations: state.conversations.filter((c) => c.id !== id),
  })),
  
  updateConversationTitle: (id, title) => set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id === id ? { ...c, title } : c
    ),
  })),
  
  setWebSocket: (ws) => set({ ws }),
  
  reset: () => set({
    currentConversationId: null,
    messages: [],
    isStreaming: false,
    streamingContent: '',
  }),
}));

