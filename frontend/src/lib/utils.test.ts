import { describe, it, expect } from 'vitest'
import { cn } from './utils'

// Unit tests focus on pure merging logic only.
describe('cn', () => {
  it('merges tailwind-ish classes and de-dupes conflicts (last wins)', () => {
    expect(cn('p-2', 'text-sm', 'p-3')).toBe('text-sm p-3')
  })

  it('skips falsy values', () => {
    expect(cn('p-2', null, undefined, false && 'x', '', 'text-sm')).toBe(
      'p-2 text-sm'
    )
  })

  it('merges conditional arrays & nested values', () => {
    expect(cn(['p-2', ['text-sm', false && 'hidden']], 'font-medium')).toBe(
      'p-2 text-sm font-medium'
    )
  })

  it('tailwind-merge resolves conflicting utilities correctly', () => {
    // tailwind-merge should ensure only the last conflicting spacing class remains
    expect(cn('px-2', 'px-4', 'px-1')).toBe('px-1')
    expect(cn('text-sm', 'text-lg', 'text-xs')).toBe('text-xs')
  })

  it('returns empty string when all inputs falsy', () => {
    expect(cn(false && 'a', null, undefined, '')).toBe('')
  })
})
