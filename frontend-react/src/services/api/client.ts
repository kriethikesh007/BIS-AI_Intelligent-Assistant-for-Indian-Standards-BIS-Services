/** Centralized API client for communicating with the Flask backend. */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

class ApiError extends Error {
  status: number;
  details?: string;

  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {}, signal } = options;

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    signal,
  };

  if (body && method !== 'GET') {
    config.body = JSON.stringify(body);
  }

  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      let details: string | undefined;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || errorMessage;
        details = errorData.details || errorData.detail;
      } catch {
        // Response wasn't JSON
      }
      throw new ApiError(errorMessage, response.status, details);
    }

    const data = await response.json();
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0,
      'Unable to connect to the server. Please check your connection.'
    );
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: { headers?: Record<string, string>; signal?: AbortSignal } | AbortSignal) => {
    if (options instanceof AbortSignal) {
      return request<T>(endpoint, { signal: options });
    }
    return request<T>(endpoint, options);
  },

  post: <T>(endpoint: string, body: unknown, options?: { headers?: Record<string, string>; signal?: AbortSignal }) =>
    request<T>(endpoint, { method: 'POST', body, ...options }),

  put: <T>(endpoint: string, body: unknown, options?: { headers?: Record<string, string> }) =>
    request<T>(endpoint, { method: 'PUT', body, ...options }),

  delete: <T>(endpoint: string, options?: { headers?: Record<string, string> }) =>
    request<T>(endpoint, { method: 'DELETE', ...options }),
};

export { ApiError };
export default apiClient;
