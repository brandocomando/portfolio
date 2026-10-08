import { QuotaStatus, ContactSubmission } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';
const CLIENT_SECRET = import.meta.env.VITE_CLIENT_SECRET || 'portfolio-client-v1';

export function getSessionId(): string {
  try {
    let sid = localStorage.getItem('portfolio_session_id');
    if (!sid) {
      const randomBytes = new Uint8Array(16);
      crypto.getRandomValues(randomBytes);
      const randomPart = Array.from(randomBytes, (b) => b.toString(16).padStart(2, '0')).join('');
      sid = 'sid_' + randomPart + Date.now().toString(36);
      localStorage.setItem('portfolio_session_id', sid);
    }
    return sid;
  } catch (e) {
    return 'fallback_session';
  }
}

export function getBaseHeaders(): Record<string, string> {
  return {
    'X-Session-ID': getSessionId(),
    'X-Portfolio-Client': CLIENT_SECRET
  };
}

export interface RetryOptions {
  maxRetries?: number;
  initialDelayMs?: number;
  maxDelayMs?: number;
  backoffFactor?: number;
  retryOnStatusCodes?: number[];
  timeoutMs?: number;
}

const DEFAULT_RETRY_STATUSES = [500, 502, 503, 504];

/**
 * Fetch wrapper with automatic exponential-backoff retries.
 * Handles Cloud Run cold starts and transient network glitches invisibly to the user,
 * logging retry attempts to console.warn.
 */
export async function fetchWithRetry(
  url: string,
  init?: RequestInit,
  options?: RetryOptions
): Promise<Response> {
  const maxRetries = options?.maxRetries ?? 3;
  const initialDelayMs = options?.initialDelayMs ?? 1000;
  const maxDelayMs = options?.maxDelayMs ?? 5000;
  const backoffFactor = options?.backoffFactor ?? 2;
  const retryStatuses = options?.retryOnStatusCodes ?? DEFAULT_RETRY_STATUSES;
  const timeoutMs = options?.timeoutMs ?? 20000;

  let attempt = 0;
  let delay = initialDelayMs;

  while (true) {
    let timeoutId: any;
    let didTimeout = false;

    try {
      attempt++;

      const controller = new AbortController();
      timeoutId = setTimeout(() => {
        didTimeout = true;
        controller.abort();
      }, timeoutMs);

      // Link external signal if present
      const callerSignal = init?.signal;
      if (callerSignal) {
        if (callerSignal.aborted) {
          throw new DOMException('Aborted', 'AbortError');
        }
        callerSignal.addEventListener('abort', () => controller.abort(), { once: true });
      }

      const response = await fetch(url, {
        ...init,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // Check if retryable server error (cold start 502/503/504)
      if (retryStatuses.includes(response.status) && attempt <= maxRetries) {
        console.warn(
          `[API Retry] Request to ${url} returned ${response.status} (likely cold start). Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})...`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * backoffFactor, maxDelayMs);
        continue;
      }

      if (attempt > 1) {
        console.info(`[API Retry] Request to ${url} recovered successfully on attempt ${attempt}.`);
      }

      return response;
    } catch (err: any) {
      if (timeoutId) clearTimeout(timeoutId);

      const isCallerAbort = init?.signal?.aborted;
      if (isCallerAbort) {
        throw err;
      }

      const isTimeout = didTimeout || err?.name === 'AbortError' || err?.name === 'TimeoutError';
      const isNetworkError =
        isTimeout ||
        err instanceof TypeError ||
        err?.message?.includes('Failed to fetch') ||
        err?.message?.includes('NetworkError') ||
        err?.message?.includes('Load failed');

      if (isNetworkError && attempt <= maxRetries) {
        const reason = isTimeout ? `timed out after ${timeoutMs}ms` : (err?.message || 'network failure');
        console.warn(
          `[API Retry] Request to ${url} failed (${reason}, likely cold start). Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})...`
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * backoffFactor, maxDelayMs);
        continue;
      }

      throw err;
    }
  }
}

export async function fetchQuota(authToken?: string | null): Promise<QuotaStatus> {
  const headers: Record<string, string> = {
    ...getBaseHeaders()
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const defaultAuthLimit = Number(import.meta.env.VITE_AUTH_DAILY_LIMIT) || 10;
  const defaultAnonLimit = Number(import.meta.env.VITE_ANON_DAILY_LIMIT) || 5;

  try {
    const res = await fetchWithRetry(
      `${API_BASE}/api/v1/leads/quota`,
      { headers },
      { maxRetries: 3, initialDelayMs: 800, timeoutMs: 15000 }
    );
    if (!res.ok) {
      return {
        authenticated: !!authToken,
        tier: authToken ? 'authenticated' : 'anonymous',
        limit: authToken ? defaultAuthLimit : defaultAnonLimit,
        remaining: authToken ? defaultAuthLimit : defaultAnonLimit,
        reset_seconds: 86400,
        auth_limit: defaultAuthLimit,
        anon_limit: defaultAnonLimit
      };
    }
    return await res.json();
  } catch (e) {
    console.warn('[API] fetchQuota failed after retries, falling back to default quota:', e);
    return {
      authenticated: !!authToken,
      tier: authToken ? 'authenticated' : 'anonymous',
      limit: authToken ? defaultAuthLimit : defaultAnonLimit,
      remaining: authToken ? defaultAuthLimit : defaultAnonLimit,
      reset_seconds: 86400,
      auth_limit: defaultAuthLimit,
      anon_limit: defaultAnonLimit
    };
  }
}

export interface StreamChatParams {
  question: string;
  history?: { role: string; content: string }[];
  authToken?: string | null;
  onSources?: (sources: any[]) => void;
  onToken?: (token: string) => void;
  onDone?: (remaining: number) => void;
  onError?: (err: any) => void;
}

export async function streamChat({
  question,
  history = [],
  authToken,
  onSources,
  onToken,
  onDone,
  onError
}: StreamChatParams): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getBaseHeaders()
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  try {
    const response = await fetchWithRetry(
      `${API_BASE}/api/v1/chat/stream`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({
          messages: history,
          question
        })
      },
      {
        maxRetries: 3,
        initialDelayMs: 1000,
        timeoutMs: 30000
      }
    );

    if (response.status === 429) {
      const errData = await response.json().catch(() => ({ detail: 'Daily quota exceeded' }));
      if (onError) onError(errData.detail || errData);
      return;
    }

    if (!response.ok || !response.body) {
      throw new Error(`Chat stream request failed with status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;

        let eventType = 'message';
        let dataStr = '';

        const eventMatch = line.match(/^event:\s*(\w+)/m);
        if (eventMatch) {
          eventType = eventMatch[1];
        }

        const dataMatch = line.match(/^data:\s*(.+)$/m);
        if (dataMatch) {
          dataStr = dataMatch[1];
        }

        try {
          const parsed = JSON.parse(dataStr);
          if (eventType === 'sources' && onSources) {
            onSources(parsed.sources || []);
          } else if (eventType === 'token' && onToken) {
            onToken(parsed.token || '');
          } else if (eventType === 'done' && onDone) {
            onDone(parsed.remaining ?? 0);
          }
        } catch (e) {
          // Fallback if raw text
          if (eventType === 'token' && onToken) {
            onToken(dataStr);
          }
        }
      }
    }
  } catch (error) {
    if (onError) onError(error);
  }
}

export async function submitContactForm(
  payload: ContactSubmission
): Promise<{ status: string; message: string }> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getBaseHeaders()
  };

  const response = await fetchWithRetry(
    `${API_BASE}/api/v1/leads/contact`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    },
    {
      maxRetries: 3,
      initialDelayMs: 1000,
      timeoutMs: 20000
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit message. Please try again.');
  }

  return await response.json();
}
