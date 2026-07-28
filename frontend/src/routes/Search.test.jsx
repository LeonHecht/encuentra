import { vi, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Search from './Search';

const { getSessionMock } = vi.hoisted(() => ({
  getSessionMock: vi.fn(),
}));

// Mock SpaceSelect to a lightweight placeholder that just renders current value
vi.mock('@/components/SpaceSelect', () => ({
  default: ({ value }) => <div>Space: {value || '(none)'}</div>,
}));

// Mock useApi to return spaces and search results deterministically
const apiMock = vi.fn(async (path) => {
  if (path === 'user/spaces') {
    return { spaces: ['public', 'org1/space-a'] };
  }
  if (path === 'search') {
    return {
      query_log_id: 'query-log-1',
      results: [
        {
          id: '1',
          title: 'Case One',
          case_year: 2025,
          snippet: 'alpha beta gamma',
          score: 0.987,
          download_url: 'https://example.com/case.pdf',
          metadata_status: 'ready',
          metadata: {
            generated_title: 'Hábeas corpus sobre libertad personal',
            court_chamber: 'Sala de lo Constitucional',
            resolution_type: 'Hábeas corpus',
            outcome: 'Petición declarada improcedente',
            legal_area_tags: ['Improcedencia', 'Libertad personal'],
            parties: {
              actors: ['Abogada solicitante'],
              favored_parties: ['NAAR'],
              defendants_or_authorities: ['Juez demandado'],
              other_relevant_parties: [],
            },
            key_legal_provisions: [{ law: 'Constitución', article: 'Art. 13', text_reference: null }],
            legal_issue_summary: 'La Sala rechazó la petición por tratarse de mera legalidad.',
            relevant_dates: [{ label: 'Resolución de improcedencia', date_text: '08/01/2025', iso_date: '2025-01-08' }],
            legal_questions: ['Limites del habeas corpus frente a valoracion probatoria'],
            confidence: { overall: 0.9, notes: null },
          },
        },
        {
          id: '2',
          title: 'Case Two',
          snippet: 'delta epsilon',
          score: 0.765,
          download_url: '',
          metadata_status: 'pending',
          metadata: null,
        },
      ],
    };
  }
  if (path === 'case-metadata') {
    return { status: 'pending', metadata: null };
  }
  if (path === 'search-feedback') {
    return { id: 'feedback-1', saved: true };
  }
  return {};
});
vi.mock('@/hooks/useApi', () => ({
  useApi: (...args) => apiMock(...args),
  apiFetch: (...args) => apiMock(...args),
}));

vi.mock('@/lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: getSessionMock,
    },
  },
}));

beforeEach(() => {
  apiMock.mockClear();
  getSessionMock.mockReset();
  window.localStorage.clear();
  window.sessionStorage.clear();
  getSessionMock.mockResolvedValue({
    data: { session: { access_token: 'test-token' } },
    error: null,
  });
});

it('loads spaces, performs search, and renders results', async () => {
  render(<MemoryRouter><Search /></MemoryRouter>);

  // After mount, spaces should be loaded and first selected
  await waitFor(() => expect(screen.getByText('Space: supreme_court')).toBeInTheDocument());

  // Type a query and trigger search
  const input = screen.getByPlaceholderText(/Ingresa las palabras/i);
  await userEvent.type(input, 'contrato');
  const button = screen.getByRole('button', { name: 'Buscar' });
  await userEvent.click(button);

  // Results render
  await screen.findByText('Hábeas corpus sobre libertad personal');
  expect(screen.getByText('Case Two')).toBeInTheDocument();
  expect(screen.getByText('Sala de lo Constitucional')).toBeInTheDocument();
  expect(screen.getByText('Petición declarada improcedente')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Abrir PDF/i })).toBeInTheDocument();
  expect(screen.queryByText(/Copiar cita/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Temas relacionados/i)).not.toBeInTheDocument();

  // Search starts with the public space without blocking on a spaces request.
  expect(apiMock).not.toHaveBeenCalledWith('user/spaces');
  expect(apiMock).toHaveBeenCalledWith('search', expect.stringMatching(/\?q=contrato/));
});

it('expands and collapses legal metadata details', async () => {
  render(<MemoryRouter><Search /></MemoryRouter>);

  await waitFor(() => expect(screen.getByText('Space: supreme_court')).toBeInTheDocument());
  await userEvent.type(screen.getByPlaceholderText(/Ingresa las palabras/i), 'libertad');
  await userEvent.click(screen.getByRole('button', { name: 'Buscar' }));

  const expand = (await screen.findAllByRole('button', { name: /Expandir información/i }))[0];
  await userEvent.click(expand);

  expect(screen.getByText('Resumen jurídico')).toBeInTheDocument();
  expect(screen.getByText('Fechas relevantes')).toBeInTheDocument();
  expect(screen.getByText('Cuestiones jurídicas')).toBeInTheDocument();

  await userEvent.click(screen.getByRole('button', { name: /Ocultar información/i }));
  expect(screen.queryByText('Resumen jurídico')).not.toBeInTheDocument();
});

it('redirects unauthenticated users to signup when searching', async () => {
  getSessionMock.mockResolvedValueOnce({
    data: { session: null },
    error: null,
  });

  render(
    <MemoryRouter initialEntries={['/search']}>
      <Routes>
        <Route path="/search" element={<Search />} />
        <Route path="/signup" element={<div>Sign up page</div>} />
      </Routes>
    </MemoryRouter>
  );

  await userEvent.click(screen.getByRole('button', { name: 'Buscar' }));

  expect(await screen.findByText('Sign up page')).toBeInTheDocument();
  expect(apiMock).not.toHaveBeenCalledWith('search', expect.anything());
});
