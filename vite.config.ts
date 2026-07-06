import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@image2model/core': path.resolve(__dirname, '../../packages/core/src'),
      '@image2model/viewer': path.resolve(__dirname, '../../packages/viewer/src'),
    },
  },
})
