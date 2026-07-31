import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// GitHub Pages project sites (username.github.io/REPO_NAME/) serve from
// a subpath, not the domain root -- set VITE_BASE_PATH at build time to
// "/REPO_NAME/" for that deployment (see deploy-pages.yml). Local dev
// and same-origin deployments (nginx) leave it unset and get "/".
export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
