import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { HeuristicBanner } from '../HeuristicBanner'

describe('HeuristicBanner', () => {
  it('renders grade A with correct label', () => {
    render(<HeuristicBanner grade="A" />)
    expect(screen.getByRole('note')).toBeInTheDocument()
    expect(screen.getByText(/A — 실측 기반/)).toBeInTheDocument()
  })

  it('renders grade B', () => {
    render(<HeuristicBanner grade="B" />)
    expect(screen.getByText(/B — in-silico 추정/)).toBeInTheDocument()
  })

  it('renders grade C', () => {
    render(<HeuristicBanner grade="C" />)
    expect(screen.getByText(/C — 검증 부족/)).toBeInTheDocument()
  })

  it('renders HEURISTIC grade', () => {
    render(<HeuristicBanner grade="HEURISTIC" />)
    expect(screen.getByText(/HEURISTIC — ranking 전용/)).toBeInTheDocument()
  })

  it('shows warnings when provided and not compact', () => {
    render(
      <HeuristicBanner
        grade="C"
        warnings={['경고 1', '경고 2']}
        compact={false}
      />
    )
    expect(screen.getByText('• 경고 1')).toBeInTheDocument()
    expect(screen.getByText('• 경고 2')).toBeInTheDocument()
  })

  it('hides warnings in compact mode', () => {
    render(
      <HeuristicBanner
        grade="C"
        warnings={['경고 1']}
        compact={true}
      />
    )
    expect(screen.queryByText('• 경고 1')).not.toBeInTheDocument()
  })

  it('has accessible aria-label', () => {
    render(<HeuristicBanner grade="HEURISTIC" />)
    const note = screen.getByRole('note')
    expect(note).toHaveAttribute('aria-label', expect.stringContaining('데이터 신뢰도 등급'))
  })

  it('shows no warnings list when warnings array is empty', () => {
    render(<HeuristicBanner grade="A" warnings={[]} />)
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })
})
