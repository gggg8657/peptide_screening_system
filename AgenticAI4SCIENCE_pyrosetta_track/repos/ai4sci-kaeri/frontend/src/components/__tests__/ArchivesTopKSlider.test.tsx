import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ArchivesTopKSlider } from '../ArchivesTopKSlider'

const API_ENTRIES = [
  {
    sequence: 'AVCKNRFWKTFTSC',
    receptor: 'SSTR2',
    iptm: 0.9757,
    ptm: 0.891,
    confidence: 0.94,
    tier: 'T3',
    selectivity_index: 1.41,
  },
]

// fetch 모킹 — /api/archives/top-k 실패 시 명시적 오류 상태를 표시한다.
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('API not implemented')))
})

describe('ArchivesTopKSlider', () => {
  it('renders the component title', async () => {
    render(<ArchivesTopKSlider />)
    expect(screen.getByText(/Archive Eval/i)).toBeInTheDocument()
  })

  it('shows API error when API fails', async () => {
    render(<ArchivesTopKSlider />)
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('API not implemented')
    })
  })

  it('shows K option buttons (5, 10, 20, 50, 100)', async () => {
    render(<ArchivesTopKSlider />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '5' })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: '10' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '20' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '50' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '100' })).toBeInTheDocument()
  })

  it('changes K on button click', async () => {
    const user = userEvent.setup()
    render(<ArchivesTopKSlider />)

    await waitFor(() => screen.getByRole('button', { name: '10' }))
    const btn10 = screen.getByRole('button', { name: '10' })
    await user.click(btn10)

    // K=10으로 변경 후 aria-pressed=true
    expect(btn10).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows Tier filter buttons T3, T2, T1', async () => {
    render(<ArchivesTopKSlider />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'T3' })).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'T2' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'T1' })).toBeInTheDocument()
  })

  it('toggles Tier filter on click', async () => {
    const user = userEvent.setup()
    render(<ArchivesTopKSlider />)

    await waitFor(() => screen.getByRole('button', { name: 'T3' }))
    const t3Btn = screen.getByRole('button', { name: 'T3' })
    // 초기 T3 활성 (aria-pressed=true)
    expect(t3Btn).toHaveAttribute('aria-pressed', 'true')
    // 클릭 → 비활성화
    await user.click(t3Btn)
    expect(t3Btn).toHaveAttribute('aria-pressed', 'false')
  })

  it('renders table with archive data', async () => {
    render(<ArchivesTopKSlider />)
    // 테이블 header
    await waitFor(() => {
      expect(screen.getByRole('table', { name: 'Archives 평가 결과' })).toBeInTheDocument()
    })
    // iPTM 컬럼 헤더
    expect(screen.getByText(/iPTM \(SSTR2\)/)).toBeInTheDocument()
  })

  it('calls onSelect callback when row is clicked', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ entries: API_ENTRIES }),
    } as Response)

    render(<ArchivesTopKSlider onSelect={onSelect} />)

    // API 데이터 로드 대기
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /AVCKNRFWKTFTSC 선택/ })).toBeInTheDocument()
    })

    // 첫 번째 데이터 행 클릭
    await user.click(screen.getByRole('button', { name: /AVCKNRFWKTFTSC 선택/ }))
    expect(onSelect).toHaveBeenCalledOnce()
  })

  it('shows SI× column header', async () => {
    render(<ArchivesTopKSlider />)
    await waitFor(() => {
      expect(screen.getByText('SI×')).toBeInTheDocument()
    })
  })
})
