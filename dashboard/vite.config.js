import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/predict': 'http://localhost:8000',
      '/health':  'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
      '/stats':   'http://localhost:8000',
    },
  },
})
