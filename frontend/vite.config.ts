/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',  // D8: Tauri 相对路径
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: false,
    exclude: ['e2e/**', 'node_modules/**'],
  },
  build: {
    // F4: CSS minify 已开启（删除 cssMinify: false）
  },
  server: {
    port: 1420,
    host: '127.0.0.1',  // H9: 仅绑定 localhost
    watch: {
      ignored: ['**/src-tauri/**'],  // 排除 Rust 编译产物，避免 EBUSY 错误
    },
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            if (proxyRes.statusCode === 307 || proxyRes.statusCode === 308) {
              const location = proxyRes.headers['location'];
              if (location && location.startsWith(API_TARGET)) {
                proxyRes.headers['location'] = location.replace(API_TARGET, '');
              }
            }
          });
        },
      },
    },
  },
})
