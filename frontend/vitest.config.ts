// Ensure Vitest uses the JS config (which sets jsdom, aliases, setup, etc.)
// Re-export the configuration from vitest.config.js to avoid divergence.
import jsConfig from './vitest.config.js'

export default jsConfig
