import { vi, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import Navbar from './Navbar';

// Mock useAuth to simulate logged-in user
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    session: {
      user: {
        id: 'user-1',
        email: 'test@example.com',
        user_metadata: { full_name: 'Test User' },
      },
    },
  }),
}));

// Mock useNavigate to observe navigation on logout
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock supabase client for logout (cover both extensionless and .ts resolution)
const signOut = vi.fn().mockResolvedValue({});
vi.mock('../lib/supabaseClient', () => ({
  supabase: { auth: { signOut } },
}));
vi.mock('../lib/supabaseClient.ts', () => ({
  supabase: { auth: { signOut } },
}));

// Mock dynamic import of useApi inside Navbar subscription tier fetch
vi.mock('../hooks/useApi.jsx', () => ({
  useApi: async () => ({ subscription_tier: 'pro' }),
}));

// ResizeObserver already globally mocked in setup.ts; ensure it's defined
if (typeof window !== 'undefined' && typeof window.ResizeObserver === 'undefined') {
  // minimal mock for tests (plain JS, no casting)
  window.ResizeObserver = class { observe(){} unobserve(){} disconnect(){} };
}

function setup() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>
  );
}

it('shows avatar button and toggles dropdown', async () => {
  setup();
  const avatarBtn = screen.getByRole('button');
  await userEvent.click(avatarBtn);
  expect(await screen.findByText('test@example.com')).toBeInTheDocument();
  // shows subscription tier badge
  expect(screen.getByText(/Plan:/)).toBeInTheDocument();
  // close on second click
  await userEvent.click(avatarBtn);
  await waitFor(() => expect(screen.queryByText('test@example.com')).not.toBeInTheDocument());
});

it('logout triggers supabase signOut and navigates to /login', async () => {
  setup();
  await userEvent.click(screen.getByRole('button')); // open dropdown
  const logoutBtn = await screen.findByText(/Cerrar/i);
  await userEvent.click(logoutBtn);
  await waitFor(() => expect(signOut).toHaveBeenCalledTimes(1));
  expect(mockNavigate).toHaveBeenCalledWith('/login');
});

it('search link requests restoring the previous search', async () => {
  setup();
  await userEvent.click(screen.getByRole('link', { name: /Buscar/i }));

  expect(mockNavigate).toHaveBeenCalledWith('/search', {
    state: { restoreSearchState: true },
  });
});

it('does not expose the uploads navigation', () => {
  setup();

  expect(screen.queryByRole('link', { name: /Subir/i })).not.toBeInTheDocument();
});
