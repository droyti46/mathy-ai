import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',               // слушать на всех интерфейсах
    port: 3000,                    // чтобы совпадало с nginx
    allowedHosts: ['mathyai.ru', 'www.mathyai.ru'] // разрешаем домены
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
});
