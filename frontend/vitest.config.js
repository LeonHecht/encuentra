import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path, { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: true,
    deps: {
      optimizer: {
        web: {
          include: ['streamdown'],
        },
      },
    },
  },
})
