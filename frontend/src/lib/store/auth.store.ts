import { create } from 'zustand';
import { api } from '@/lib/api/axios';

/** Типы бэкенда: см. openapi (регистрация/логин/пара токенов) 
 * /api/auth/register -> UserOut
 * /api/auth/login    -> TokenPair  :contentReference[oaicite:0]{index=0}
 */
type User = { id: string; login: string; name?: string | null };
type TokenPair = { access_token: string; refresh_token: string; token_type?: string };

type AuthState = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  hydrate: () => void;
  setTokens: (a: string, r: string) => void;
  logout: () => void;
  registerAndLogin: (login: string, password: string, name?: string) => Promise<void>;
  login: (login: string, password: string) => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  refreshToken: null,

  hydrate: () => {
    const raw = localStorage.getItem('auth');
    if (raw) {
      const { accessToken, refreshToken } = JSON.parse(raw);
      set({ accessToken, refreshToken });
    }
  },

  setTokens: (access_token, refresh_token) => {
    localStorage.setItem('auth', JSON.stringify({ accessToken: access_token, refreshToken: refresh_token }));
    set({ accessToken: access_token, refreshToken: refresh_token });
  },

  logout: () => {
    localStorage.removeItem('auth');
    set({ user: null, accessToken: null, refreshToken: null });
  },

  registerAndLogin: async (login, password, name) => {
    await api.post('/api/auth/register', { login, password, name });  // 200 -> UserOut  :contentReference[oaicite:1]{index=1}
    const { data } = await api.post<TokenPair>('/api/auth/login', { login, password }); // -> TokenPair :contentReference[oaicite:2]{index=2}
    set({ accessToken: data.access_token, refreshToken: data.refresh_token });
    localStorage.setItem('auth', JSON.stringify({ accessToken: data.access_token, refreshToken: data.refresh_token }));
  },

  login: async (login, password) => {
    const { data } = await api.post<TokenPair>('/api/auth/login', { login, password }); // :contentReference[oaicite:3]{index=3}
    localStorage.setItem('auth', JSON.stringify({ accessToken: data.access_token, refreshToken: data.refresh_token }));
    set({ accessToken: data.access_token, refreshToken: data.refresh_token });
  },
}));
