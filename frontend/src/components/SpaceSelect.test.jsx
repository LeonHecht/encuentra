import { vi, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import SpaceSelect from './SpaceSelect';

// Mock the Radix-based select components with simple DOM elements
vi.mock('@/components/ui/select', () => ({
  Select: ({ children }) => <div data-testid="select">{children}</div>,
  SelectTrigger: ({ children }) => <div>{children}</div>,
  SelectValue: ({ placeholder }) => <span>{placeholder}</span>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectGroup: ({ children }) => <section>{children}</section>,
  SelectLabel: ({ children }) => <h4>{children}</h4>,
  SelectSeparator: () => <hr />,
  SelectItem: ({ children }) => <div role="option">{children}</div>,
}));

// Mock useSpaces to provide deterministic groups and labels
vi.mock('@/hooks/useSpaces', () => ({
  useSpaces: () => ({
    loading: false,
    user: { email: 'me@example.com', organization: 'org1' },
    spaces: [
      'public_corpus',
      'me@example.com/private-a',
      'org1/space-b',
      'other@team.com/shared-c',
    ],
    label: (s) => s.replace('me@example.com/', 'personal/'),
  }),
}));

test('renders grouped spaces with labels', () => {
  render(<SpaceSelect value={''} onChange={() => {}} allowCreate placeholder="Selecciona" />);

  // Group headers
  expect(screen.getByText('Public')).toBeInTheDocument();
  expect(screen.getByText('Personal')).toBeInTheDocument();
  expect(screen.getByText('Organisation')).toBeInTheDocument();

  // Items appear with transformed labels
  expect(screen.getByRole('option', { name: 'public_corpus' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'personal/private-a' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'org1/space-b' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'other@team.com/shared-c' })).toBeInTheDocument();

  // New space option exists when allowCreate
  expect(screen.getByText('➕ New space…')).toBeInTheDocument();
});
