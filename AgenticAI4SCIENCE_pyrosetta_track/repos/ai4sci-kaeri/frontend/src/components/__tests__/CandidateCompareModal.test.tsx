import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CandidateCompareModal } from '../CandidateCompareModal'
import type { Candidate } from '../../types'

// useFocusTrap은 실제 DOM 조작 없이 단순 ref 사용 — 모킹 불필요
// focusTrap 내부에서 document 쿼리를 하므로 jest-dom 환경에서는 동작 무관

function makeCandidate(overrides: Partial<Candidate> & { id: string }): Candidate {
  const { id, ...rest } = overrides
  return {
    rank: 1,
    id,
    sequence: 'AGCKNFFWKTFTSC',
    ddG: -4.5,
    totalScore: -600,
    clashScore: 2.3,
    finalScore: 38,
    result: 'PASS',
    ...rest,
  }
}

describe('CandidateCompareModal', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing with 2 candidates', () => {
    const candidates = [
      makeCandidate({ id: 'cand01', sequence: 'AGCKNFFWKTFTSC' }),
      makeCandidate({ id: 'cand03', sequence: 'AGCKNRFWKTFTSC', ddG: -3.1 }),
    ]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('shows candidate IDs in header columns', () => {
    const candidates = [
      makeCandidate({ id: 'cand01' }),
      makeCandidate({ id: 'cand03' }),
    ]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    expect(screen.getByText('cand01')).toBeInTheDocument()
    expect(screen.getByText('cand03')).toBeInTheDocument()
  })

  it('marks first candidate as reference (기준)', () => {
    const candidates = [
      makeCandidate({ id: 'cand01' }),
      makeCandidate({ id: 'cand03' }),
    ]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    expect(screen.getByText('(기준)')).toBeInTheDocument()
  })

  it('calls onClose when X button is clicked', async () => {
    const user = userEvent.setup()
    const candidates = [makeCandidate({ id: 'cand01' }), makeCandidate({ id: 'cand03' })]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)

    const closeBtn = screen.getByRole('button', { name: '비교 모달 닫기' })
    await user.click(closeBtn)
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('calls onClose when Escape key is pressed', async () => {
    const user = userEvent.setup()
    const candidates = [makeCandidate({ id: 'cand01' }), makeCandidate({ id: 'cand03' })]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)

    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })

  it('shows HEURISTIC warning footer', () => {
    const candidates = [makeCandidate({ id: 'cand01' }), makeCandidate({ id: 'cand03' })]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    expect(screen.getByText(/HL score는 후보/)).toBeInTheDocument()
  })

  it('renders sequence diff rows', () => {
    const candidates = [
      makeCandidate({ id: 'cand01', sequence: 'AGCKNFFWKTFTSC' }),
      makeCandidate({ id: 'cand03', sequence: 'AGCKNRFWKTFTSC' }),
    ]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    // aria-label으로 서열 확인
    expect(screen.getByLabelText('AGCKNFFWKTFTSC')).toBeInTheDocument()
    expect(screen.getByLabelText('AGCKNRFWKTFTSC')).toBeInTheDocument()
  })

  it('renders nothing when candidates array is empty', () => {
    const { container } = render(
      <CandidateCompareModal candidates={[]} onClose={onClose} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows comparison table with attribute rows', () => {
    const candidates = [makeCandidate({ id: 'cand01' }), makeCandidate({ id: 'cand03' })]
    render(<CandidateCompareModal candidates={candidates} onClose={onClose} />)
    const table = screen.getByRole('table', { name: '후보 속성 비교 테이블' })
    expect(within(table).getByText('ΔΔG (kcal/mol)')).toBeInTheDocument()
    expect(within(table).getByText('Total Score')).toBeInTheDocument()
    expect(within(table).getByText('Clash Score')).toBeInTheDocument()
  })
})
