import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./hooks/usePipelineStatus', () => ({
  usePipelineStatus: () => ({
    executionMode: 'full',
    runId: '',
    startedAt: '',
    updatedAt: '',
    iteration: 0,
    totalIterations: 5,
    llmModel: '',
    target: '',
    reference: '',
    steps: [],
    rosettaSubsteps: [],
    timeline: [],
    agents: [],
    candidates: [],
    historicalCandidates: [],
    qcGates: [],
    convergence: [],
    liveApis: { esmfold: 'pending', molmim: 'pending' },
    bestCandidate: null,
    molecules: [],
    visualizationImages: [],
    completed: false,
    connected: false,
    error: null,
    archivedRuns: [],
    viewingArchive: null,
    switchRun: vi.fn(),
  }),
}))

vi.mock('./pages/RunConsolePage', () => ({ RunConsolePage: () => <MockPage name="Run Console" /> }))
vi.mock('./pages/SelectivityExplorerPage', () => ({ SelectivityExplorerPage: () => <MockPage name="Selectivity Explorer" /> }))
vi.mock('./pages/ManualSelectivityPage', () => ({ ManualSelectivityPage: () => <MockPage name="Manual Selectivity" /> }))
vi.mock('./pages/CandidatePage', () => ({ CandidatePage: () => <MockPage name="Candidate Review" /> }))
vi.mock('./pages/RunLauncherPage', () => ({ RunLauncherPage: () => <MockPage name="Run Launcher" /> }))
vi.mock('./pages/StrategyRunnerPage', () => ({ StrategyRunnerPage: () => <MockPage name="Strategy Runner" /> }))
vi.mock('./pages/BenchmarkPage', () => ({ BenchmarkPage: () => <MockPage name="Benchmark" /> }))
vi.mock('./pages/WetlabOrderPage', () => ({ WetlabOrderPage: () => <MockPage name="Wetlab" /> }))
vi.mock('./pages/BindingPocketPage', () => ({ BindingPocketPage: () => <MockPage name="Binding Pocket" /> }))
vi.mock('./pages/SettingsPage', () => ({ SettingsPage: () => <MockPage name="Settings" /> }))
vi.mock('./pages/AboutPage', () => ({ AboutPage: () => <MockPage name="About" /> }))
vi.mock('./pages/SiloAPage', () => ({ SiloAPage: () => <MockPage name="Silo A" /> }))
vi.mock('./pages/SiloBPage', () => ({ SiloBPage: () => <MockPage name="Silo B" /> }))
vi.mock('./pages/CombinedPage', () => ({ CombinedPage: () => <MockPage name="Combined" /> }))
vi.mock('./pages/SelectivityPage', () => ({ SelectivityPage: () => <MockPage name="Legacy Selectivity" /> }))

function MockPage({ name }: { name: string }) {
  return (
    <section aria-label={`${name} smoke page`}>
      <h2>{name} Page</h2>
      <button type="button">{name} action</button>
    </section>
  )
}

describe('App route smoke', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/console')
  })

  it('renders primary navigation routes and clickable page actions', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByRole('heading', { name: 'Run Console Page' })
    expect(screen.getByRole('button', { name: 'Run Console action' })).toBeEnabled()

    const primaryRoutes = [
      ['Selectivity', 'Selectivity Explorer Page', 'Selectivity Explorer action'],
      ['Manual Selectivity', 'Manual Selectivity Page', 'Manual Selectivity action'],
      ['Candidate Review', 'Candidate Review Page', 'Candidate Review action'],
      ['Run Launcher', 'Run Launcher Page', 'Run Launcher action'],
      ['Strategy Runner', 'Strategy Runner Page', 'Strategy Runner action'],
    ] as const

    for (const [linkName, heading, action] of primaryRoutes) {
      await user.click(screen.getByRole('link', { name: linkName }))
      await screen.findByRole('heading', { name: heading })
      expect(screen.getByRole('button', { name: action })).toBeEnabled()
    }
  })

  it('opens More menu and routes to secondary pages', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByRole('heading', { name: 'Run Console Page' })
    const more = screen.getByRole('button', { name: /more/i })
    await user.click(more)

    expect(screen.getByRole('menu')).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Benchmark' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Settings' })).toBeInTheDocument()

    await user.click(screen.getByRole('menuitem', { name: 'Settings' }))
    await screen.findByRole('heading', { name: 'Settings Page' })
    expect(screen.getByRole('button', { name: 'Settings action' })).toBeEnabled()

    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })
})
