/**
 * useFlexPepDockJob — stub 관련 유닛 테스트
 *
 * isStubResults: selectivity_matrix 내 stub 항목 감지 헬퍼
 */
import { describe, it, expect } from 'vitest'
import { isStubResults } from '../useFlexPepDockJob'
import type { FlexPepDockResults } from '../useFlexPepDockJob'

// ─── 픽스처 ────────────────────────────────────────────────────────────────

function makeResults(rows: { stub?: boolean }[]): FlexPepDockResults {
  return {
    selectivity_matrix: rows.map((r, i) => ({
      receptor: ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'][i % 5] as 'SSTR1',
      dG_kcal_mol: -8.0,
      interface_score: -35.0,
      pass: true,
      stub: r.stub,
    })),
    selectivity_index: 0.0,
    pdb_paths: [],
  }
}

// ─── 테스트 ────────────────────────────────────────────────────────────────

describe('isStubResults', () => {
  it('모든 행이 stub=true 이면 true 반환', () => {
    const results = makeResults([{ stub: true }, { stub: true }])
    expect(isStubResults(results)).toBe(true)
  })

  it('하나라도 stub=true 이면 true 반환 (부분 stub)', () => {
    const results = makeResults([{ stub: undefined }, { stub: true }, { stub: undefined }])
    expect(isStubResults(results)).toBe(true)
  })

  it('모든 행에 stub 필드가 없으면 false 반환 (실 PyRosetta 결과)', () => {
    const results = makeResults([{}, {}, {}])
    expect(isStubResults(results)).toBe(false)
  })

  it('stub=false 명시 행은 false 처리', () => {
    // BE가 stub:false 를 명시하는 경우(미래 호환) — 현재 실 실행 시 필드 자체가 없으나 타입 커버
    const results = makeResults([{ stub: false }, { stub: false }])
    expect(isStubResults(results)).toBe(false)
  })

  it('matrix 가 비어 있으면 false 반환', () => {
    const results = makeResults([])
    expect(isStubResults(results)).toBe(false)
  })
})
