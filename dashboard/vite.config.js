import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true },
    host: true,
    port: 3000,
    proxy: {
      '/predict': 'http://api:8000',
      '/health':  'http://api:8000',
      '/metrics': 'http://api:8000',
      '/stats':   'http://api:8000',
    },
  },
})
