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

export async function fetchQuota(authToken?: string | null): Promise<QuotaStatus> {
  const headers: Record<string, string> = {
    ...getBaseHeaders()
  };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const defaultAuthLimit = Number(import.meta.env.VITE_AUTH_DAILY_LIMIT) || 30;
  const defaultAnonLimit = Number(import.meta.env.VITE_ANON_DAILY_LIMIT) || 10;

  try {
    const res = await fetch(`${API_BASE}/api/v1/leads/quota`, { headers });
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
    const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        messages: history,
        question
      })
    });

    if (response.status === 429) {
      const errData = await response.json();
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

  const response = await fetch(`${API_BASE}/api/v1/leads/contact`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit message. Please try again.');
  }

  return await response.json();
}
