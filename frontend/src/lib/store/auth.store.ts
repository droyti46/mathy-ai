import { create } from 'zustand';
import { api } from '@/lib/api/axios';

type User = { id: string; login: string; name?: string | null };
type TokenPair = { access_token: string; refresh_token: string; token_type?: string };

type AuthState = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  hydrate: () => void;
  setTokens: (a: string, r: string) => void;
  setUser: (u: User | null) => void;
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

  setUser: (u) => set({ user: u }),              // ← добавлено

  logout: () => {
    localStorage.removeItem('auth');
    set({ user: null, accessToken: null, refreshToken: null });
  },

  registerAndLogin: async (login, password, name) => {
    await api.post('/api/auth/register', { login, password, name });
    const { data } = await api.post<TokenPair>('/api/auth/login', { login, password });
    set({ accessToken: data.access_token, refreshToken: data.refresh_token });
    localStorage.setItem('auth', JSON.stringify({ accessToken: data.access_token, refreshToken: data.refresh_token }));
  },

  login: async (login, password) => {
    const { data } = await api.post<TokenPair>('/api/auth/login', { login, password });
    localStorage.setItem('auth', JSON.stringify({ accessToken: data.access_token, refreshToken: data.refresh_token }));
    set({ accessToken: data.access_token, refreshToken: data.refresh_token });
  },
}));
