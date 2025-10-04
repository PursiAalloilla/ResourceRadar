import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables from .env files
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],

    // Make sure preview works on Heroku or any container
    preview: {
      host: '0.0.0.0',
      port: 4173,
      allowedHosts: ['*'],
    },

    // Optionally expose your API URL to the app
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL),
    },
  }
})