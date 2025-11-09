import { vi, it, expect, beforeAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
// Mock heavy routes before importing App to avoid pulling CSS from deps
vi.mock('./routes/Chat', () => ({
  default: () => <div>MockChat</div>,
}));
vi.mock('./routes/Uploads', () => ({
  default: () => <div>MockUploads</div>,
}));

// Mock AuthPage to prevent importing supabaseClient during test collection
vi.mock('./routes/AuthPage', () => ({
  default: () => <div>MockAuth</div>,
}));

// IMPORTANT: defer importing App until after mocks so that any modules like supabaseClient
// don't initialize before we provide env vars/mocks.
let App;
beforeAll(async () => {
  App = (await import('./App')).default;
});

// Mock components that depend on auth and external libs to keep this a pure smoke test
vi.mock('./components/Navbar', () => ({
  default: () => <nav>MockNav</nav>,
}));

vi.mock('./routes/Landing', () => ({
  default: () => <div>MockLanding</div>,
}));

// Mock hooks imports referenced deeper (Search imports useApi with alias)
vi.mock('@/hooks/useApi', () => ({
  useApi: async () => ({ spaces: [] }),
  apiFetch: async () => ({ spaces: [] }),
}));
vi.mock('@/hooks/useSpaces', () => ({ useSpaces: () => ({ spaces: [], loading: false, label: (s) => s }) }));
vi.mock('@/components/SpaceSelect', () => ({ default: () => <div /> }));

it('renders App shell with Navbar and Landing route', async () => {
  render(
    <MemoryRouter initialEntries={["/"]}>
      <App />
    </MemoryRouter>
  );

  expect(screen.getByText('MockNav')).toBeInTheDocument();
  expect(screen.getByText('MockLanding')).toBeInTheDocument();
});
