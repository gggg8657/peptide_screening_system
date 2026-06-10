import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { CandidatePage } from '../CandidatePage'
import {
  useADMET,
  useCand03Variants,
  useCandidates,
  useRuns,
  useRunStatus,
  useTransitionWetlabOrder,
} from '../../hooks/dashboard'
import type { Candidate as DashboardCandidate } from '../../hooks/dashboard'

vi.mock('../../components/dashboard/Molstar', () => ({
  Molstar: ({ pdbUrl }: { pdbUrl?: string }) => <div data-testid="molstar">{pdbUrl ?? 'no-pdb'}</div>,
}))

vi.mock('../../components/dashboard/Sequence', () => ({
  Sequence: ({ seq }: { seq: string }) => <span>{seq}</span>,
}))

vi.mock('../../components/dashboard/TierBadge', () => ({
  TierBadge: ({ tier }: { tier: string }) => <span>{tier}</span>,
}))

vi.mock('../../contexts/PipelineContext', () => ({
  usePipelineContext: () => ({ runId: 'RUN-1', viewingArchive: null }),
}))

vi.mock('../../hooks/dashboard', () => ({
  useADMET: vi.fn(),
  useCand03Variants: vi.fn(),
  useCandidates: vi.fn(),
  useRuns: vi.fn(),
  useRunStatus: vi.fn(),
  useTransitionWetlabOrder: vi.fn(),
}))

const run1Candidates: DashboardCandidate[] = [
  {
    id: 'PRST-001',
    seq: 'AGCKNFFWKTFTSC',
    tier: 'T2',
    margin: 0.08,
    best_receptor: 'SSTR2',
    iptm: { SSTR1: 0.81, SSTR2: 0.96, SSTR3: 0.79, SSTR4: 0.82, SSTR5: 0.84 },
    ddg: -12.4,
    source: 'runs_local/RUN-1/PRST-001.pdb',
    mutations: [],
    recommended: true,
    wildtype: false,
    notes: null,
  },
  {
    id: 'PRST-002',
    seq: 'AGCKNYYWKTFTSC',
    tier: 'T1',
    margin: 0.12,
    best_receptor: 'SSTR2',
    iptm: { SSTR1: 0.78, SSTR2: 0.94, SSTR3: 0.77, SSTR4: 0.81, SSTR5: 0.82 },
    ddg: -9.1,
    source: 'runs_local/RUN-1/PRST-002.pdb',
    mutations: ['F6->Y', 'F7->Y'],
    recommended: false,
    wildtype: false,
    notes: null,
  },
]

const run2Candidates: DashboardCandidate[] = [
  {
    id: 'PRST-101',
    seq: 'AGCKNAAWKTFTSC',
    tier: 'T2',
    margin: 0.2,
    best_receptor: 'SSTR2',
    iptm: { SSTR1: 0.73, SSTR2: 0.97, SSTR3: 0.76, SSTR4: 0.77, SSTR5: 0.79 },
    ddg: -13.2,
    source: 'runs_local/RUN-2/PRST-101.pdb',
    mutations: ['F6->A', 'F7->A'],
    recommended: true,
    wildtype: false,
    notes: null,
  },
]

function setupMocks(options: { runs?: Array<{ run_id: string; started_at: string; completed: boolean; n_candidates: number; best_ddg: number | null }> } = {}) {
  const runs = options.runs ?? [
    { run_id: 'RUN-1', started_at: '2026-05-21T00:00:00Z', completed: true, n_candidates: 2, best_ddg: -12.4 },
    { run_id: 'RUN-2', started_at: '2026-05-21T01:00:00Z', completed: true, n_candidates: 1, best_ddg: -13.2 },
  ]
  vi.mocked(useRuns).mockReturnValue({
    data: { runs },
    isLoading: false,
  } as unknown as ReturnType<typeof useRuns>)
  vi.mocked(useRunStatus).mockImplementation((runId) => ({
    data: { run_id: runId ?? 'RUN-1' },
    isLoading: false,
  }) as unknown as ReturnType<typeof useRunStatus>)
  vi.mocked(useCandidates).mockImplementation((runId) => ({
    data: {
      run_id: runId ?? 'RUN-1',
      wild_type: 'AGCKNFFWKTFTSC',
      candidates: runId === 'RUN-2' ? run2Candidates : run1Candidates,
    },
    isLoading: false,
  }) as unknown as ReturnType<typeof useCandidates>)
  vi.mocked(useCand03Variants).mockReturnValue({
    data: { variants: [] },
  } as unknown as ReturnType<typeof useCand03Variants>)
  vi.mocked(useADMET).mockReturnValue({
    data: {
      half_life_minutes: 45,
      instability: 25,
      boman_kcal: 0.3,
      aggregation_score: 0.15,
      gravy: 0.2,
      confidence: 'TEST',
      vulnerabilities: [],
    },
    isLoading: false,
  } as unknown as ReturnType<typeof useADMET>)
  vi.mocked(useTransitionWetlabOrder).mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useTransitionWetlabOrder>)
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url === '/api/runs/RUN-2') {
      return Response.json({ run_id: 'RUN-2', candidates: run2Candidates })
    }
    if (url === '/api/runs/RUN-1') {
      return Response.json({ run_id: 'RUN-1', candidates: run1Candidates })
    }
    return Response.json({})
  }))
}

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}{location.search}</div>
}

function renderPage(initialEntry = '/candidate?run_id=RUN-1', options?: Parameters<typeof setupMocks>[0]) {
  setupMocks(options)
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/candidate" element={<><CandidatePage /><LocationProbe /></>} />
        <Route path="/candidate/:id" element={<><CandidatePage /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

describe('CandidatePage 2-level selectors', () => {
  it('renders the header run selector and body candidate selector', () => {
    renderPage()

    const runSelector = screen.getByRole('combobox', { name: /run selector/i })
    expect(runSelector).toBeInTheDocument()
    expect(within(runSelector).getByRole('option', { name: 'RUN-1 · 2 candidates' })).toBeInTheDocument()
    expect(within(runSelector).getByRole('option', { name: 'RUN-2 · 1 candidates' })).toBeInTheDocument()

    const candidateSelector = screen.getByRole('group', { name: /candidate selector/i })
    expect(within(candidateSelector).getByRole('button', { name: '1' })).toHaveAttribute('title', 'PRST-001')
    expect(within(candidateSelector).getByRole('button', { name: '2' })).toHaveAttribute('title', 'PRST-002')
  })

  it('updates candidate-specific content when the selection changes', async () => {
    const user = userEvent.setup()
    renderPage()

    const candidateSelector = screen.getByRole('group', { name: /candidate selector/i })
    await user.click(within(candidateSelector).getByRole('button', { name: '2' }))

    expect(within(candidateSelector).getByRole('button', { name: '2' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getAllByText('AGCKNYYWKTFTSC').length).toBeGreaterThan(0)
    expect(screen.getByText('margin +0.120')).toBeInTheDocument()
    expect(screen.getByTestId('molstar')).toHaveTextContent('PRST-002.pdb')
  })

  it('syncs the default candidate query parameter on initial load and user changes', async () => {
    const user = userEvent.setup()
    renderPage('/candidate?run_id=RUN-1')

    expect(screen.getByTestId('location')).toHaveTextContent('/candidate?run_id=RUN-1&candidate=PRST-001')

    await user.click(within(screen.getByRole('group', { name: /candidate selector/i })).getByRole('button', { name: '2' }))

    expect(screen.getByTestId('location')).toHaveTextContent('/candidate?run_id=RUN-1&candidate=PRST-002')
  })

  it('changes runs from the header selector and navigates to the first candidate of that run', async () => {
    const user = userEvent.setup()
    renderPage('/candidate?run_id=RUN-1&candidate=PRST-001')

    await user.selectOptions(screen.getByRole('combobox', { name: /run selector/i }), 'RUN-2')

    expect(await screen.findByText('margin +0.200')).toBeInTheDocument()
    expect(screen.getByTestId('location')).toHaveTextContent('/candidate?run_id=RUN-2&candidate=PRST-101')
    expect(screen.getByTestId('molstar')).toHaveTextContent('PRST-101.pdb')
  })

  it('disables the run selector when no runs are available', () => {
    renderPage('/candidate?run_id=RUN-1', { runs: [] })

    expect(screen.getByRole('combobox', { name: /run selector/i })).toBeDisabled()
  })
})
