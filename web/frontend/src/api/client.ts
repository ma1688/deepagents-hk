/**
 * API client for HKEX Agent backend
 */

const API_BASE = '/api';

// Helper for API requests
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// ==================== Config API ====================

export const configApi = {
  getModels: () => 
    apiRequest<{ models: import('@/types').ModelOption[] }>('/config/models'),
  
  getModelsByProvider: (provider: string) =>
    apiRequest<{ models: import('@/types').ModelOption[] }>(`/config/models/${provider}`),
  
  getConfig: (userId: string) =>
    apiRequest<import('@/types').UserConfig>(`/config/${userId}`),
  
  updateConfig: (userId: string, data: Partial<import('@/types').UserConfig> & { apiKey?: string }) =>
    apiRequest<import('@/types').UserConfig>(`/config/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({
        provider: data.provider,
        model_name: data.modelName,
        api_key: data.apiKey,
        base_url: data.baseUrl,
        temperature: data.temperature,
        max_tokens: data.maxTokens,
      }),
    }),
  
  deleteApiKey: (userId: string) =>
    apiRequest<{ status: string }>(`/config/${userId}/api-key`, { method: 'DELETE' }),
  
  testConfig: (userId: string) =>
    apiRequest<{ status: string; message: string; testResponse: string }>(`/config/${userId}/test`, { method: 'POST' }),
};

// ==================== History API ====================

export const historyApi = {
  getConversations: (userId: string, limit = 50) =>
    apiRequest<import('@/types').ConversationListItem[]>(`/history/${userId}/conversations?limit=${limit}`),
  
  createConversation: (userId: string, title = '新对话') =>
    apiRequest<import('@/types').Conversation>(`/history/${userId}/conversations`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
  
  getConversation: (userId: string, conversationId: string) =>
    apiRequest<import('@/types').Conversation>(`/history/${userId}/conversations/${conversationId}`),
  
  updateConversation: (userId: string, conversationId: string, title: string) =>
    apiRequest<import('@/types').Conversation>(`/history/${userId}/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    }),
  
  deleteConversation: (userId: string, conversationId: string) =>
    apiRequest<{ status: string }>(`/history/${userId}/conversations/${conversationId}`, { method: 'DELETE' }),
  
  getTokenStats: (userId: string, days = 30) =>
    apiRequest<import('@/types').TokenUsageSummary>(`/history/${userId}/stats?days=${days}`),
};

// ==================== Search API ====================

export const searchApi = {
  searchAnnouncements: (data: {
    stockCode: string;
    fromDate: string;
    toDate: string;
    title?: string;
    market?: string;
    rowRange?: number;
  }) =>
    apiRequest<import('@/types').SearchResult>('/search/announcements', {
      method: 'POST',
      body: JSON.stringify({
        stock_code: data.stockCode,
        from_date: data.fromDate,
        to_date: data.toDate,
        title: data.title,
        market: data.market || 'SEHK',
        row_range: data.rowRange || 100,
      }),
    }),
  
  getRecentAnnouncements: (stockCode: string, days = 30) =>
    apiRequest<import('@/types').SearchResult>(`/search/stock/${stockCode}/recent?days=${days}`),
};

// ==================== WebSocket ====================

export function createChatWebSocket(userId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return new WebSocket(`${protocol}//${host}/ws/chat/ws/${userId}`);
}

