import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend serves /api and /images. Override with API_URL if it
// runs somewhere other than uvicorn's default port.
const apiUrl = process.env.API_URL ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': apiUrl,
      '/images': apiUrl,
    },
  },
})
