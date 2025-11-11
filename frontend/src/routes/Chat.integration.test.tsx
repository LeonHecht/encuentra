import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

// Mock Response component to avoid streamdown complexity
vi.mock('@/components/ai-elements/response', () => ({ 
  Response: ({ children }: any) => <div>{children}</div> 
}))

// Route-level integration: mock only external/service boundaries
vi.mock('@/components/Navbar', () => ({ default: () => <nav>MockNav</nav> }))
vi.mock('@/components/ChatSidebar', () => ({ default: () => <aside>MockSidebar</aside> }))
vi.mock('@/components/SpaceSelect', () => ({ default: (props: any) => <select aria-label="space-select" value={props.value} onChange={e => props.onChange(e.target.value)} /> }))

import App from '@/App'

vi.mock('@/lib/supabaseClient', () => {
  const builder = (table: string) => ({
    select() { return this },
    order() { return Promise.resolve({ data: [], error: null }) },
    eq() { return this },
    single() { return Promise.resolve({ data: table === 'chats' ? { id: 'chat1', agent_state: null } : { agent_state: null }, error: null }) },
    insert() { if (table === 'chats') { return { select: () => ({ single: () => Promise.resolve({ data: { id: 'chat1', title: 't' }, error: null }) }) } } return Promise.resolve({ data: null, error: null }) },
    update() { return Promise.resolve({ data: null, error: null }) },
    delete() { return Promise.resolve({ data: null, error: null }) },
  })
  return {
    supabase: {
      auth: {
        getUser: vi.fn().mockResolvedValue({ data: { user: { id: 'u1' } } }),
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      },
      from: (table: string) => builder(table),
    },
  }
})

function sseStream(frames: { event: string, data: any }[]) {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const f of frames) {
        const chunk = `event:${f.event}\ndata:${JSON.stringify(f.data)}\n\n`
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url.includes('/v1/chat/agentic/stream')) {
      return Promise.resolve({ ok: true, body: sseStream([
        { event: 'response.output_text.delta', data: { delta: 'Hola!' } },
        { event: 'response.completed', data: { answer: 'Hola!', citations: [] } },
      ]) }) as any
    }
    if (url.includes('/v1/user/spaces')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ spaces: ['public'] }) }) as any
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any
  }))
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Chat route integration', () => {
  it('navigates to /chat and handles a full user -> assistant exchange', async () => {
    render(
      <MemoryRouter initialEntries={["/chat"]}>
        <App />
      </MemoryRouter>
    )

    // Chat placeholder visible
    expect(await screen.findByText(/Hola, ¿cómo puedo ayudarte hoy\?/)).toBeInTheDocument()

    // Type and send a message
    const textarea = screen.getByPlaceholderText(/Pregunta lo que quieras/)
    await userEvent.type(textarea, 'Prueba')
    const submitBtn = screen.getByRole('button', { name: /submit/i })
    await userEvent.click(submitBtn)

    // User echo appears
    await screen.findByText('Prueba')

    // Assistant answer appears after streaming
    await waitFor(() => expect(screen.getAllByText('Hola!').length).toBeGreaterThan(0))
  })
})
