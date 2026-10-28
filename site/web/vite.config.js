import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// В dev-режиме запросы /api уходят в server.py (порт 8765), который проксирует Ollama.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
})
