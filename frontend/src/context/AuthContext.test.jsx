import { vi, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuth } from './AuthContext';

// Mock supabase client
vi.mock('../lib/supabaseClient', () => {
  return {
    supabase: {
      auth: {
        getSession: () => Promise.resolve({ data: { session: { user: { id: 'u1', user_metadata: { full_name: 'Test User' }, email: 'test@example.com' } } } }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
      },
    },
  };
});

function ShowUser() {
  const { session } = useAuth();
  return <div>{session?.user?.email || 'no-user'}</div>;
}

it('provides session from supabase mock', async () => {
  render(
    <AuthProvider>
      <ShowUser />
    </AuthProvider>
  );

  await waitFor(() => expect(screen.getByText('test@example.com')).toBeInTheDocument());
});
