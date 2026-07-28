import { vi, it, expect, describe, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'
import Search from './Search'

const { getSessionMock } = vi.hoisted(() => ({
  getSessionMock: vi.fn(),
}))

// Mock SpaceSelect to a simple <select>
vi.mock('@/components/SpaceSelect', () => ({
  __esModule: true,
  default: ({ value, onChange }) => (
    <select aria-label="space" value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="public">public</option>
    </select>
  ),
}))

// Spy-able mock for useApi
const apiMock = vi.fn(async (path, qs = '') => {
  if (path === 'user/spaces') return { spaces: ['public'] }

  if (path === 'search') {
    const q = new URLSearchParams(qs.replace(/^\?/, '')).get('q') || ''
    if (q === 'derecho') {
      return {
        query_log_id: 'query-log-1',
        results: [
          { id: 'doc-1', title: 'Sentencia 123/2020', score: 0.87, snippet: 'derecho constitucional' },
        ],
      }
    }
    if (q === 'nohits') return { query_log_id: 'query-log-empty', results: [] }
    return { query_log_id: 'query-log-empty', results: [] }
  }

  if (path === 'search-feedback') {
    return { id: 'feedback-1', saved: true }
  }
  return {}
})
vi.mock('@/hooks/useApi', () => ({
  useApi: (...args) => apiMock(...args),
  apiFetch: (...args) => apiMock(...args),
}))

vi.mock('@/lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: getSessionMock,
    },
  },
}))

const renderSearch = () => render(
  <MemoryRouter>
    <Search />
  </MemoryRouter>
)

describe('<Search />', () => {
  beforeEach(() => {
    apiMock.mockClear()
    getSessionMock.mockReset()
    window.sessionStorage.clear()
    window.localStorage.clear()
    getSessionMock.mockResolvedValue({
      data: { session: { access_token: 'test-token' } },
      error: null,
    })
  })

  it('ignores blank queries (no search, no empty-state)', async () => {
    renderSearch()

    // The route renders immediately with the public space.
    await waitFor(() => expect(screen.getByText(/Buscar casos/i)).toBeInTheDocument())
    expect(apiMock).not.toHaveBeenCalledWith('user/spaces')

    const btn = screen.getByRole('button', { name: /buscar/i })
    await userEvent.click(btn)
    // No search should run for an empty query.
    expect(apiMock.mock.calls.filter(c => c[0] === 'search').length).toBe(0)
    // Searched flag stayed false, so no empty-state
    expect(screen.queryByText(/No se encontraron resultados\./)).not.toBeInTheDocument()
  })

  it('runs a real search and renders a result', async () => {
    renderSearch()
    await screen.findByText(/Buscar casos/)

    const input = screen.getByPlaceholderText(/Ingresa las palabras/i)
    const btn   = screen.getByRole('button', { name: /buscar/i })

    await userEvent.type(input, 'derecho')
    await userEvent.click(btn)
    await screen.findByText(/Sentencia 123\/2020/)
    expect(screen.getByText(/derecho constitucional/)).toBeInTheDocument()
    expect(screen.queryByText(/Score:/)).not.toBeInTheDocument()
  })

  it('saves feedback for a displayed search result', async () => {
    renderSearch()
    await screen.findByText(/Buscar casos/)

    await userEvent.type(screen.getByPlaceholderText(/Ingresa las palabras/i), 'derecho')
    await userEvent.click(screen.getByRole('button', { name: /buscar/i }))
    await screen.findByText(/Sentencia 123\/2020/)

    await userEvent.click(screen.getByRole('button', { name: /Marcar resultado como útil/i }))

    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledWith(
        'search-feedback',
        '',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"query_log_id":"query-log-1"'),
        })
      )
    })
    const feedbackCall = apiMock.mock.calls.find((call) => call[0] === 'search-feedback')
    const payload = JSON.parse(feedbackCall[2].body)
    expect(payload).toMatchObject({
      query_text: 'derecho',
      space: 'supreme_court',
      doc_id: 'doc-1',
      rank: 1,
      score: 0.87,
      feedback: 'positive',
    })
  })

  it('shows empty state when query has zero hits', async () => {
    renderSearch()
    await screen.findByText(/Buscar casos/)

    const input = screen.getByPlaceholderText(/Ingresa las palabras/i)
    const btn   = screen.getByRole('button', { name: /buscar/i })

    await userEvent.type(input, 'nohits')
    await userEvent.click(btn)

    await screen.findByText(/No se encontraron resultados\./)
  })

  it('restores the previous search when navigation requests it', async () => {
    window.sessionStorage.setItem('encuentra.searchState', JSON.stringify({
      q: 'derecho',
      space: 'public',
      topK: '10',
      year: '2020',
      searched: true,
      results: [
        { id: 'doc-1', title: 'Sentencia 123/2020', score: 0.87, snippet: 'derecho constitucional' },
      ],
    }))

    render(
      <MemoryRouter initialEntries={[{ pathname: '/search', state: { restoreSearchState: true } }]}>
        <Search />
      </MemoryRouter>
    )

    expect(await screen.findByDisplayValue('derecho')).toBeInTheDocument()
    expect(screen.getByDisplayValue('2020')).toBeInTheDocument()
    expect(screen.getByText(/Sentencia 123\/2020/)).toBeInTheDocument()
  })
})
