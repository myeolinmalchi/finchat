import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target:
          'http://ec2-3-34-52-134.ap-northeast-2.compute.amazonaws.com:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    },
  },
});
