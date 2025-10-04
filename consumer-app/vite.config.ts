import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: [
      'emergency-consumer-app-8f712de6c168.herokuapp.com',
      'localhost'
    ],
    host: '0.0.0.0',
    port: 4173
  }
})
