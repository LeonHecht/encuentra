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
      // Mock CSS imports to empty modules
      'streamdown/style.css': path.resolve(
        __dirname,
        './src/test/mocks/empty.js'
      ),
      'katex/dist/katex.min.css': path.resolve(
        __dirname,
        './src/test/mocks/empty.js'
      ),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false, // Disable CSS processing entirely in tests
    deps: {
      optimizer: {
        web: {
          include: ['streamdown'],
        },
      },
    },
  },
})
