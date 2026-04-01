import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: true, // Expose to local network
    port: 5173,
  }
})
