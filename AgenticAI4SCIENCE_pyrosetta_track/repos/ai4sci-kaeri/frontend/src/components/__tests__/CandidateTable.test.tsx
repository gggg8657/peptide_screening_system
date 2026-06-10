import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CandidateTable } from '../CandidateTable'
import type { Candidate } from '../../types'

// Mock fetch globally to prevent network calls from useAdmetBatch / useValidation
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ results: [] }),
  }))
})

function makeCandidates(n: number): Candidate[] {
  return Array.from({ length: n }, (_, i) => ({
    rank: i + 1,
    id: `MUT-${String(i + 1).padStart(3, '0')}`,
    sequence: `AGCKNFFWKTFTS${String.fromCharCode(65 + i)}`,
    ddG: -(15 + i * 3),
    totalScore: -(600 + i * 20),
    clashScore: 1 + i,
    finalScore: 40 - i * 2,
    result: i % 2 === 0 ? 'PASS' as const : 'FAIL' as const,
    failReason: i % 2 === 1 ? 'ddG gate failed' : undefined,
  }))
}

/** Helper: get the desktop table element (hidden on mobile, visible on sm+) */
function getDesktopTable() {
  return screen.getByRole('table', { name: 'Candidate scores' })
}

describe('CandidateTable', () => {
  it('renders table with candidate rows', () => {
    const candidates = makeCandidates(3)
    render(<CandidateTable candidates={candidates} />)

    expect(screen.getByText('Candidate Ranking')).toBeInTheDocument()
    expect(screen.getByText(/3 candidates/)).toBeInTheDocument()

    // Check IDs are rendered in desktop table
    const table = getDesktopTable()
    expect(within(table).getByText('MUT-001')).toBeInTheDocument()
    expect(within(table).getByText('MUT-002')).toBeInTheDocument()
    expect(within(table).getByText('MUT-003')).toBeInTheDocument()
  })

  it('renders column headers', () => {
    render(<CandidateTable candidates={makeCandidates(1)} />)

    const table = getDesktopTable()
    expect(within(table).getByText('Rank')).toBeInTheDocument()
    expect(within(table).getByText('ΔG')).toBeInTheDocument()
    expect(within(table).getByText('Total Score')).toBeInTheDocument()
    expect(within(table).getByText('Clash')).toBeInTheDocument()
    expect(within(table).getByText('Final Score')).toBeInTheDocument()
  })

  it('renders PASS/FAIL badges in table rows', () => {
    const candidates = makeCandidates(2) // [PASS, FAIL]
    render(<CandidateTable candidates={candidates} />)

    const table = getDesktopTable()
    const tbody = within(table).getAllByRole('row').slice(1) // skip header row
    // PASS badge in first row, FAIL badge in second row
    expect(within(tbody[0]).getByText('PASS')).toBeInTheDocument()
    expect(within(tbody[1]).getByText('FAIL')).toBeInTheDocument()
  })

  it('shows 3D button when onView3D is provided', () => {
    const onView3D = vi.fn()
    render(<CandidateTable candidates={makeCandidates(1)} onView3D={onView3D} />)

    const btns = screen.getAllByTitle(/View 3D structure/)
    expect(btns.length).toBeGreaterThanOrEqual(1)
  })

  it('does not show 3D column without onView3D', () => {
    render(<CandidateTable candidates={makeCandidates(1)} />)
    expect(screen.queryByTitle(/View 3D structure/)).not.toBeInTheDocument()
  })

  it('shows checkboxes for selection', () => {
    render(<CandidateTable candidates={makeCandidates(2)} />)

    // Desktop: "Select all" + 2 row checkboxes = 3
    // Mobile: 2 row checkboxes = 2
    // Total = 5
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes.length).toBe(5)
  })

  it('sort button changes on click', async () => {
    const user = userEvent.setup()
    render(<CandidateTable candidates={makeCandidates(3)} />)

    const table = getDesktopTable()
    const ddgHeader = within(table).getByText('ΔG').closest('th')!
    await user.click(ddgHeader)

    // After clicking ΔG column, it should be the active sort column (aria-sort)
    expect(ddgHeader).toHaveAttribute('aria-sort', 'ascending')
  })

  it('checkbox click toggles selection', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<CandidateTable candidates={makeCandidates(2)} onSelectionChange={onChange} />)

    // Get checkboxes within the desktop table
    const table = getDesktopTable()
    const checkboxes = within(table).getAllByRole('checkbox')
    // Click first row checkbox (index 1, since 0 is "select all")
    await user.click(checkboxes[1])

    expect(onChange).toHaveBeenCalled()
  })

  it('renders filter buttons', () => {
    render(<CandidateTable candidates={makeCandidates(3)} />)

    expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'PASS' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'FAIL' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'REF' })).toBeInTheDocument()
  })

  it('pagination shows correct range', () => {
    render(<CandidateTable candidates={makeCandidates(5)} />)
    expect(screen.getByText(/Showing 1–5 of 5/)).toBeInTheDocument()
  })

  it('renders mobile card view', () => {
    render(<CandidateTable candidates={makeCandidates(2)} />)

    // Mobile card view should be present (role="list")
    const cardList = screen.getByRole('list', { name: 'Candidate cards' })
    const cards = within(cardList).getAllByRole('listitem')
    expect(cards.length).toBe(2)
  })

  it('ClashCell renders colorblind-safe icons', () => {
    // Low clash (green + check icon)
    const candidates = makeCandidates(1)
    candidates[0].clashScore = 2.5
    render(<CandidateTable candidates={candidates} />)

    const table = getDesktopTable()
    // Check icon should be present (lucide check has specific class)
    const clashCell = within(table).getByText('2.50').closest('span')!
    expect(clashCell.querySelector('svg')).toBeInTheDocument()
  })
})
