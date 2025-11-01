import axios from 'axios';
import { useAuthStore } from '@/lib/store/auth.store';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
});

let isRefreshing = false;
let waiters: Array<() => void> = [];

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const { refreshToken, setTokens, logout } = useAuthStore.getState();

    if (error.response?.status === 401 && refreshToken) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const { data } = await axios.post(
            `${api.defaults.baseURL}/api/auth/refresh`,
            null,
            { params: { refresh_token: refreshToken } }
          );
          setTokens(data.access_token, data.refresh_token);
        } catch {
          logout();
          return Promise.reject(error);
        } finally {
          isRefreshing = false;
          waiters.forEach((fn) => fn());
          waiters = [];
        }
      } else {
        await new Promise<void>((res) => waiters.push(res));
      }
      const cfg = error.config!;
      cfg.headers.Authorization = `Bearer ${useAuthStore.getState().accessToken}`;
      return api(cfg);
    }
    return Promise.reject(error);
  }
);
