import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react({
    babel: { plugins: [['babel-plugin-react-compiler']] },
  })],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // <-- FastAPI, not Ollama
        changeOrigin: true,
        // keep or remove; with this, /api/chat -> /chat on the backend
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
