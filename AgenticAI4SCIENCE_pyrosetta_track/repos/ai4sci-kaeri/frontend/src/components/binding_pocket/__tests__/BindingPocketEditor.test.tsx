/**
 * BindingPocketEditor 테스트
 *
 * 위치: src/components/binding_pocket/__tests__/BindingPocketEditor.test.tsx
 *
 * 테스트 항목:
 *   1. 좌표 입력 → state 업데이트 (미저장 배지 표시)
 *   2. radius slider 5~30 Å 범위 속성 검증
 *   3. 잔기 ID 추가 (Enter / + 버튼) 및 제거
 *   4. 저장 클릭 → useUpdateBindingPocket mutation 호출
 *   5. PDB 자동 추출 버튼 → useExtractBindingPocket mutation({ receptor, residue_ids }) 호출
 *   6. 잔기 없이 추출 시 인라인 오류 메시지 표시
 *   7. 기본값 복원 버튼 → useDeleteBindingPocket mutation 호출
 *   + 접근성 검증
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BindingPocketEditor } from '../BindingPocketEditor'
import {
  useBindingPocket,
  useUpdateBindingPocket,
  useExtractBindingPocket,
  useDeleteBindingPocket,
} from '../../../hooks/useBindingPocket'
import type { BindingPocketConfig } from '../../../hooks/useBindingPocket'

// ── vi.mock은 vitest에 의해 파일 최상단으로 호이스팅됨 ───────────────────────
vi.mock('../../../hooks/useBindingPocket')

// ─────────────────────────────────────────────────────────────────────────────
// 픽스처

const mockConfig: BindingPocketConfig = {
  receptor: 'SSTR2',
  center_x: -6.2,
  center_y: 14.8,
  center_z: 2.1,
  radius_angstrom: 17.0,
  residue_ids: [202, 205, 208, 284, 285, 287, 288],
  source: 'PDB_3SST',
}

// ─────────────────────────────────────────────────────────────────────────────
// 공통 mock 설정

const mockMutateAsync = vi.fn().mockResolvedValue({ ok: true, path: '/data/sstr2.json' })
const mockExtractAsync = vi.fn().mockResolvedValue(mockConfig)
const mockDeleteAsync = vi.fn().mockResolvedValue({ ok: true, restored: true })

/** mutation mock 공통 필드 */
function baseMutationMock<T extends (...args: unknown[]) => unknown>(fn: T) {
  return {
    mutateAsync: fn,
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    isSuccess: false,
    isIdle: true,
    error: null,
    reset: vi.fn(),
    variables: undefined,
    context: undefined,
    data: undefined,
    failureCount: 0,
    failureReason: null,
    status: 'idle' as const,
    submittedAt: 0,
  }
}

beforeEach(() => {
  vi.clearAllMocks()

  vi.mocked(useBindingPocket).mockReturnValue({
    data: mockConfig,
    isLoading: false,
    isError: false,
    isPending: false,
    status: 'success',
  } as ReturnType<typeof useBindingPocket>)

  vi.mocked(useUpdateBindingPocket).mockReturnValue(
    baseMutationMock(mockMutateAsync) as unknown as ReturnType<typeof useUpdateBindingPocket>,
  )

  vi.mocked(useExtractBindingPocket).mockReturnValue(
    baseMutationMock(mockExtractAsync) as unknown as ReturnType<typeof useExtractBindingPocket>,
  )

  vi.mocked(useDeleteBindingPocket).mockReturnValue(
    baseMutationMock(mockDeleteAsync) as unknown as ReturnType<typeof useDeleteBindingPocket>,
  )
})

// ─────────────────────────────────────────────────────────────────────────────
// 테스트

describe('BindingPocketEditor', () => {
  // ── 1. 좌표 입력 → state 업데이트 ────────────────────────────────────────
  describe('좌표 입력', () => {
    it('X축 좌표를 변경하면 미저장 배지가 표시된다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // 초기 상태: 미저장 배지 없음
      expect(screen.queryByText('미저장 변경사항')).not.toBeInTheDocument()

      const xInput = screen.getByLabelText(/SSTR2 포켓 중심 X축 좌표/)
      await user.clear(xInput)
      await user.type(xInput, '-10.5')

      // 변경 후: 미저장 배지 표시
      expect(screen.getByText('미저장 변경사항')).toBeInTheDocument()
    })

    it('Y, Z축 좌표 입력 필드가 모두 렌더링된다', () => {
      render(<BindingPocketEditor />)

      expect(
        screen.getByLabelText(/SSTR2 포켓 중심 X축 좌표/),
      ).toBeInTheDocument()
      expect(
        screen.getByLabelText(/SSTR2 포켓 중심 Y축 좌표/),
      ).toBeInTheDocument()
      expect(
        screen.getByLabelText(/SSTR2 포켓 중심 Z축 좌표/),
      ).toBeInTheDocument()
    })

    it('로드된 API 데이터가 좌표 필드에 반영된다', () => {
      render(<BindingPocketEditor />)

      const xInput = screen.getByLabelText(
        /SSTR2 포켓 중심 X축 좌표/,
      ) as HTMLInputElement

      expect(parseFloat(xInput.value)).toBeCloseTo(-6.2, 3)
    })
  })

  // ── 2. radius slider 범위 검증 ────────────────────────────────────────────
  describe('반경 슬라이더', () => {
    it('min=5, max=30 속성을 갖는다', () => {
      render(<BindingPocketEditor />)

      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })
      expect(slider).toHaveAttribute('min', '5')
      expect(slider).toHaveAttribute('max', '30')
    })

    it('aria-valuemin/max/now 속성이 정확하다', () => {
      render(<BindingPocketEditor />)

      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })
      expect(slider).toHaveAttribute('aria-valuemin', '5')
      expect(slider).toHaveAttribute('aria-valuemax', '30')
      // 로드된 mockConfig.radius_angstrom = 17.0
      expect(slider).toHaveAttribute('aria-valuenow', '17')
    })

    it('슬라이더를 변경하면 반경 값이 업데이트된다', () => {
      render(<BindingPocketEditor />)

      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })
      fireEvent.change(slider, { target: { value: '20' } })

      // 반경 표시가 업데이트됨
      expect(screen.getByText('20.0 Å')).toBeInTheDocument()
    })

    it('박스 크기가 radius × 2 또는 최소 30으로 자동 계산된다', () => {
      render(<BindingPocketEditor />)

      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })

      // radius=10 → box=20 < 30 → 표시는 30.0
      fireEvent.change(slider, { target: { value: '10' } })
      expect(screen.getAllByText('30.0').length).toBeGreaterThan(0)

      // radius=20 → box=40 → 표시는 40.0
      fireEvent.change(slider, { target: { value: '20' } })
      expect(screen.getAllByText('40.0').length).toBeGreaterThan(0)
    })
  })

  // ── 3. 잔기 ID 추가/제거 ──────────────────────────────────────────────────
  describe('잔기 ID 관리', () => {
    it('Enter 키로 포켓 중심 잔기를 추가할 수 있다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      const pocketInput = screen.getByLabelText(
        /포켓 중심 잔기 번호 입력/,
      ) as HTMLInputElement

      await user.type(pocketInput, '999')
      await user.keyboard('{Enter}')

      // 칩으로 표시됨
      expect(screen.getByLabelText('잔기 999 제거')).toBeInTheDocument()
      // 입력 필드 초기화
      expect(pocketInput.value).toBe('')
    })

    it('+ 버튼으로 선택성 잔기를 추가할 수 있다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      const selectivityInput = screen.getByLabelText(
        /선택성 잔기 번호 입력/,
      ) as HTMLInputElement
      await user.type(selectivityInput, '999')

      const addBtn = screen.getByRole('button', { name: '선택성 잔기 추가' })
      await user.click(addBtn)

      expect(screen.getByLabelText('잔기 999 제거')).toBeInTheDocument()
      expect(selectivityInput.value).toBe('')
    })

    it('× 버튼으로 잔기를 제거할 수 있다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // mockConfig에 202가 있음 (pocket 그룹 첫 번째)
      const removeBtn = screen.getByLabelText('잔기 202 제거')
      expect(removeBtn).toBeInTheDocument()

      await user.click(removeBtn)

      expect(screen.queryByLabelText('잔기 202 제거')).not.toBeInTheDocument()
    })

    it('중복 잔기는 추가되지 않는다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // 202는 이미 mockConfig에 존재
      const pocketInput = screen.getByLabelText(/포켓 중심 잔기 번호 입력/)
      await user.type(pocketInput, '202')
      await user.keyboard('{Enter}')

      // 잔기 202 제거 버튼이 1개만 있어야 함
      const removeBtns = screen.getAllByLabelText('잔기 202 제거')
      expect(removeBtns).toHaveLength(1)
    })
  })

  // ── 4. 저장 → mutation 호출 ───────────────────────────────────────────────
  describe('저장', () => {
    it('변경 후 저장 클릭 시 useUpdateBindingPocket.mutateAsync가 호출된다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // 변경사항 만들기 (dirty 상태 필요)
      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })
      fireEvent.change(slider, { target: { value: '20' } })

      const saveBtn = screen.getByRole('button', {
        name: /SSTR2 바인딩 포켓 설정 저장/,
      })
      await user.click(saveBtn)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledTimes(1)
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            receptor: 'SSTR2',
            radius_angstrom: 20,
          }),
        )
      })
    })

    it('변경사항 없이는 저장 버튼이 비활성화된다', () => {
      render(<BindingPocketEditor />)

      const saveBtn = screen.getByRole('button', {
        name: /SSTR2 바인딩 포켓 설정 저장/,
      })
      expect(saveBtn).toBeDisabled()
    })

    it('초기화 버튼 클릭 시 변경사항이 롤백되고 저장 버튼이 비활성화된다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // 변경
      const slider = screen.getByRole('slider', {
        name: /SSTR2 포켓 반경 슬라이더/,
      })
      fireEvent.change(slider, { target: { value: '25' } })
      expect(screen.getByText('미저장 변경사항')).toBeInTheDocument()

      // 초기화
      const resetBtn = screen.getByRole('button', { name: '변경사항 초기화' })
      await user.click(resetBtn)

      expect(screen.queryByText('미저장 변경사항')).not.toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /저장/ }),
      ).toBeDisabled()
    })
  })

  // ── 5. PDB 자동 추출 → extract mutation({ receptor, residue_ids }) 호출 ────
  describe('PDB 자동 추출', () => {
    it('자동 추출 버튼 클릭 시 {receptor, residue_ids}와 함께 mutation이 호출된다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      // mockConfig.residue_ids = [202,205,208,284,285,287,288]
      // splitResidues → pocket=[202,205,208,284,285], selectivity=[287,288]
      // 합산 = [202,205,208,284,285,287,288]

      const extractBtn = screen.getByRole('button', {
        name: /SSTR2 PDB 파일에서 포켓 좌표 자동 추출/,
      })
      await user.click(extractBtn)

      await waitFor(() => {
        expect(mockExtractAsync).toHaveBeenCalledTimes(1)
        expect(mockExtractAsync).toHaveBeenCalledWith({
          receptor: 'SSTR2',
          residue_ids: expect.arrayContaining([202, 205, 208, 287, 288]),
        })
      })
    })

    it('잔기가 없을 때 추출 클릭 시 인라인 오류 메시지가 표시된다', async () => {
      const user = userEvent.setup()

      // 잔기 없는 config
      vi.mocked(useBindingPocket).mockReturnValue({
        data: { ...mockConfig, residue_ids: [] as number[] },
        isLoading: false,
        isError: false,
        isPending: false,
        status: 'success',
      } as unknown as ReturnType<typeof useBindingPocket>)

      render(<BindingPocketEditor />)

      const extractBtn = screen.getByRole('button', {
        name: /SSTR2 PDB 파일에서 포켓 좌표 자동 추출/,
      })
      await user.click(extractBtn)

      expect(
        screen.getByRole('alert'),
      ).toHaveTextContent('잔기를 하나 이상 입력해야')

      // mutation은 호출되지 않아야 함
      expect(mockExtractAsync).not.toHaveBeenCalled()
    })

    it('추출 중에는 버튼이 비활성화된다', () => {
      vi.mocked(useExtractBindingPocket).mockReturnValue({
        ...baseMutationMock(mockExtractAsync),
        isPending: true,
      } as unknown as ReturnType<typeof useExtractBindingPocket>)

      render(<BindingPocketEditor />)

      const extractBtn = screen.getByRole('button', {
        name: /SSTR2 PDB 파일에서 포켓 좌표 자동 추출/,
      })
      expect(extractBtn).toBeDisabled()
    })
  })

  // ── 7. 기본값 복원 (DELETE) ────────────────────────────────────────────────
  describe('기본값 복원', () => {
    it('기본값 복원 버튼 클릭 시 useDeleteBindingPocket.mutateAsync가 receptor와 함께 호출된다', async () => {
      const user = userEvent.setup()
      render(<BindingPocketEditor />)

      const deleteBtn = screen.getByRole('button', {
        name: /SSTR2 서버 설정 삭제 및 기본값 복원/,
      })
      await user.click(deleteBtn)

      await waitFor(() => {
        expect(mockDeleteAsync).toHaveBeenCalledTimes(1)
        expect(mockDeleteAsync).toHaveBeenCalledWith('SSTR2')
      })
    })

    it('복원 중에는 버튼이 비활성화된다', () => {
      vi.mocked(useDeleteBindingPocket).mockReturnValue({
        ...baseMutationMock(mockDeleteAsync),
        isPending: true,
      } as unknown as ReturnType<typeof useDeleteBindingPocket>)

      render(<BindingPocketEditor />)

      const deleteBtn = screen.getByRole('button', {
        name: /SSTR2 서버 설정 삭제 및 기본값 복원/,
      })
      expect(deleteBtn).toBeDisabled()
    })
  })

  // ── 접근성 ────────────────────────────────────────────────────────────────
  describe('접근성', () => {
    it('수용체 탭이 role="tablist" + role="tab"을 갖는다', () => {
      render(<BindingPocketEditor />)

      expect(screen.getByRole('tablist', { name: '수용체 선택' })).toBeInTheDocument()
      const tabs = screen.getAllByRole('tab')
      expect(tabs).toHaveLength(5)
    })

    it('SSTR2 탭이 aria-selected="true"로 표시된다', () => {
      render(<BindingPocketEditor />)

      const sstr2Tab = screen.getByRole('tab', { name: /SSTR2/ })
      expect(sstr2Tab).toHaveAttribute('aria-selected', 'true')
    })

    it('폼에 role="form" + aria-label이 있다', () => {
      render(<BindingPocketEditor />)

      expect(
        screen.getByRole('form', { name: /SSTR2 바인딩 포켓 설정/ }),
      ).toBeInTheDocument()
    })

    it('로딩 중에는 폼 대신 로딩 인디케이터가 표시된다', () => {
      vi.mocked(useBindingPocket).mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        isPending: true,
        status: 'pending',
      } as ReturnType<typeof useBindingPocket>)

      render(<BindingPocketEditor />)

      expect(screen.getByText(/포켓 설정 로딩 중/)).toBeInTheDocument()
      expect(screen.queryByRole('form')).not.toBeInTheDocument()
    })
  })
})
