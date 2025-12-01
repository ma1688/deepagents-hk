/**
 * Authentication API client
 */

const API_BASE = '/api';

interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email?: string;
  username?: string;
  is_guest: boolean;
}

interface UserResponse {
  id: string;
  email?: string;
  username?: string;
  is_guest: boolean;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

// Helper for API requests with auth
async function authRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers,
    ...options,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

export const authApi = {
  /**
   * Register a new user
   */
  register: (email: string, username: string, password: string) =>
    authRequest<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    }),
  
  /**
   * Login with email/username and password
   */
  login: (emailOrUsername: string, password: string) =>
    authRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email_or_username: emailOrUsername, password }),
    }),
  
  /**
   * Create a guest user
   */
  createGuest: () =>
    authRequest<AuthResponse>('/auth/guest', {
      method: 'POST',
    }),
  
  /**
   * Get current user info
   */
  getCurrentUser: (token: string) =>
    authRequest<UserResponse>('/auth/me', {}, token),
  
  /**
   * Upgrade guest to full account
   */
  upgradeGuest: (token: string, email: string, username: string, password: string) =>
    authRequest<AuthResponse>('/auth/upgrade', {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    }, token),
  
  /**
   * Refresh access token
   */
  refresh: (token: string) =>
    authRequest<AuthResponse>('/auth/refresh', {
      method: 'POST',
    }, token),
};

