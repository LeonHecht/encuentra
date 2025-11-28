// Vitest + Testing Library setup
// Extends expect() with jest-dom matchers
import '@testing-library/jest-dom/vitest'

// Optional: lightweight DOM APIs that some components/libraries expect
// matchMedia is commonly accessed by UI libs or custom hooks
if (typeof window !== 'undefined' && !window.matchMedia) {
  // minimal mock that satisfies most use-cases
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(window as any).matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {}, // deprecated
    removeListener: () => {}, // deprecated
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })
}

// Provide a minimal ResizeObserver mock for components that measure layout
if (typeof window !== 'undefined' && !(window as any).ResizeObserver) {
  class MockResizeObserver {
    callback: ResizeObserverCallback
    constructor(cb: ResizeObserverCallback) {
      this.callback = cb
    }
    observe() {
      /* no-op */
    }
    unobserve() {
      /* no-op */
    }
    disconnect() {
      /* no-op */
    }
  }
  ;(window as any).ResizeObserver =
    MockResizeObserver as unknown as typeof ResizeObserver
}

// --- MSW server lifecycle for integration tests ---
// Only initialize in test environment (Vitest)
import { server } from './msw/server'
import { beforeAll, afterEach, afterAll } from 'vitest'

// Start server before all tests, reset handlers after each, close after all.
// Vitest's global hooks are available because we set globals: true in vitest config.
beforeAll(() => {
  // Guard if server is undefined (e.g., unit tests tree-shaken?)
  if (server?.listen) server.listen({ onUnhandledRequest: 'warn' })
})
afterEach(() => {
  if (server?.resetHandlers) server.resetHandlers()
})
afterAll(() => {
  if (server?.close) server.close()
})
