// src/lib/api/stream.ts
import { api } from '@/lib/api/axios';
import { useAuthStore } from '@/lib/store/auth.store';

export interface StreamOptions {
  onStart?: () => void;
  onDone?: () => void;
  onError?: (e: unknown) => void; // <-- добавили
}

/** Делает абсолютный URL из относительного на базу axios */
export function toAbsUrl(url: string) {
  const base = (api.defaults.baseURL || '').replace(/\/$/, '');
  if (/^https?:\/\//i.test(url)) return url;
  return url.startsWith('/') ? `${base}${url}` : `${base}/${url}`;
}

/** Один раз пытаемся рефрешнуть токен и повторить запрос, если был 401 */
export async function fetchWithAuthOnce(url: string, body: any): Promise<Response> {
  const doFetch = async () => {
    const token = useAuthStore.getState().accessToken;
    return fetch(toAbsUrl(url), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body ?? {}),
    });
  };

  let res = await doFetch();
  if (res.status !== 401) return res;

  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) return res;

  try {
    const { data } = await api.post('/api/auth/refresh', null, {
      params: { refresh_token: refreshToken },
    });
    setTokens(data.access_token, data.refresh_token);
  } catch {
    logout();
    return res;
  }
  return doFetch();
}

/** Универсальный стрим с авторизацией */
export async function streamText(
  url: string,
  body: any,
  onChunk: (text: string) => void,
  opts: StreamOptions = {}
) {
  try {
    opts.onStart?.();

    const res = await fetchWithAuthOnce(url, body);
    if (!res.ok) throw new Error(`HTTP ${res.status} ${await res.text().catch(() => '')}`);
    if (!res.body) throw new Error('Empty body');

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }

    opts.onDone?.();
  } catch (e) {
    opts.onError?.(e); // <-- теперь тип знает про onError
    throw e;
  }
}
