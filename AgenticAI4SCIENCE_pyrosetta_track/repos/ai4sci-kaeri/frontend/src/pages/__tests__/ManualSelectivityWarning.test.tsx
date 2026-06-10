import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { computeEstimatedSeconds, LargeJobWarningBanner } from '../ManualSelectivityPage'

describe('computeEstimatedSeconds', () => {
  it('nReceptors × nstruct × cycles × 30 을 반환한다', () => {
    expect(computeEstimatedSeconds(2, 10, 5)).toBe(3000)   // 2*10*5*30
    expect(computeEstimatedSeconds(3, 50, 10)).toBe(45000) // 3*50*10*30
    expect(computeEstimatedSeconds(1, 1, 1)).toBe(30)
  })
})

describe('LargeJobWarningBanner', () => {
  it('nstruct > 20 이면 경고 배너가 표시된다', () => {
    render(<LargeJobWarningBanner nstruct={21} nReceptors={1} cycles={10} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/nstruct\/receptors로 시작 권장/)).toBeInTheDocument()
  })

  it('nReceptors > 2 이면 경고 배너가 표시된다', () => {
    render(<LargeJobWarningBanner nstruct={5} nReceptors={3} cycles={10} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('예상 시간(h)과 6h timeout 메시지를 포함한다', () => {
    // 2 receptors × 30 nstruct × 10 cycles × 30s = 18000s = 5.0h
    render(<LargeJobWarningBanner nstruct={30} nReceptors={2} cycles={10} />)
    expect(screen.getByText(/5\.0h 예상/)).toBeInTheDocument()
    expect(screen.getByText(/6h timeout/)).toBeInTheDocument()
  })

  it('nstruct ≤ 20 이고 nReceptors ≤ 2 이면 렌더링하지 않는다', () => {
    const { container } = render(
      <LargeJobWarningBanner nstruct={20} nReceptors={2} cycles={10} />,
    )
    expect(container.firstChild).toBeNull()
  })
})
