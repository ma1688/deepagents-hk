// User types
export interface User {
  id: string;
  createdAt: string;
}

// Message types
export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  tokenCount?: number;
  createdAt: string;
}

// Conversation types
export interface Conversation {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: Message[];
}

export interface ConversationListItem {
  id: string;
  userId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

// Config types
export interface UserConfig {
  id: string;
  userId: string;
  provider: 'siliconflow' | 'openai' | 'anthropic';
  modelName: string;
  baseUrl?: string;
  temperature: number;
  maxTokens: number;
  hasApiKey: boolean;
  updatedAt: string;
}

export interface ModelOption {
  provider: string;
  modelName: string;
  displayName: string;
  contextLimit: number;
  pricePerMillion?: number;
}

// Search types
export interface AnnouncementItem {
  title: string;
  date: string;
  url?: string;
  category?: string;
}

export interface SearchResult {
  stockCode: string;
  totalCount: number;
  announcements: AnnouncementItem[];
  cached: boolean;
  cacheExpiresAt?: string;
}

// Token stats types
export interface TokenStats {
  id: string;
  date: string;
  modelName: string;
  inputTokens: number;
  outputTokens: number;
  costYuan: number;
}

export interface TokenUsageSummary {
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCostYuan: number;
  dailyStats: TokenStats[];
}

// WebSocket message types
export interface WSMessage {
  type: 'content' | 'error' | 'done' | 'info';
  content?: string;
  conversationId?: string;
  messageId?: string;
  tokenCount?: number;
}

// Chat request
export interface ChatRequest {
  message: string;
  conversationId?: string;
}

