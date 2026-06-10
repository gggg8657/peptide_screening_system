/**
 * P04: pipelineStateFlags 단위 테스트
 * - completed=true → isActiveRun=false
 * - updatedAt 60s 이상 경과 → isStale=true
 * - 상태 우선순위 및 각 상태 독립성 검증
 */

import { describe, it, expect } from 'vitest'
import { computePipelineStateFlags } from '../pipelineStateFlags'

// 기본 live 상태 (Active Run 상태)
const activeRunBase = {
  connected: true,
  completed: false,
  steps: [{ id: 'step01' }],
  viewingArchive: null,
  updatedAt: new Date(Date.now() - 5_000).toISOString(), // 5초 전
}

const NOW = Date.now()

describe('computePipelineStateFlags', () => {
  // ── isActiveRun ─────────────────────────────────────────────────────────
  describe('isActiveRun', () => {
    it('connected=true, completed=false, steps>0 → isActiveRun=true', () => {
      const flags = computePipelineStateFlags(activeRunBase, NOW)
      expect(flags.isActiveRun).toBe(true)
    })

    it('completed=true → isActiveRun=false (P04 핵심)', () => {
      const live = { ...activeRunBase, completed: true }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isActiveRun).toBe(false)
    })

    it('connected=false → isActiveRun=false', () => {
      const live = { ...activeRunBase, connected: false }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isActiveRun).toBe(false)
    })

    it('steps=[] → isActiveRun=false', () => {
      const live = { ...activeRunBase, steps: [] }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isActiveRun).toBe(false)
    })
  })

  // ── isArchive ────────────────────────────────────────────────────────────
  describe('isArchive', () => {
    it('viewingArchive != null → isArchive=true', () => {
      const live = { ...activeRunBase, viewingArchive: 'run-archive-01' }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isArchive).toBe(true)
    })

    it('viewingArchive=null → isArchive=false', () => {
      const flags = computePipelineStateFlags(activeRunBase, NOW)
      expect(flags.isArchive).toBe(false)
    })
  })

  // ── isCompletedSnapshot ──────────────────────────────────────────────────
  describe('isCompletedSnapshot', () => {
    it('connected=true, completed=true, viewingArchive=null → isCompletedSnapshot=true', () => {
      const live = { ...activeRunBase, completed: true }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isCompletedSnapshot).toBe(true)
    })

    it('completed=true + viewingArchive → isCompletedSnapshot=false (archive 우선)', () => {
      const live = { ...activeRunBase, completed: true, viewingArchive: 'run-01' }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isCompletedSnapshot).toBe(false)
      expect(flags.isArchive).toBe(true)
    })

    it('completed=false → isCompletedSnapshot=false', () => {
      const flags = computePipelineStateFlags(activeRunBase, NOW)
      expect(flags.isCompletedSnapshot).toBe(false)
    })
  })

  // ── isStale ──────────────────────────────────────────────────────────────
  describe('isStale', () => {
    it('updatedAt 60초 이상 경과 → isStale=true (P04 핵심)', () => {
      const staleTime = new Date(NOW - 61_000).toISOString()
      const live = { ...activeRunBase, updatedAt: staleTime }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isStale).toBe(true)
    })

    it('updatedAt 정확히 60초 전 → isStale=false (경계: > 60_000 이므로)', () => {
      const staleTime = new Date(NOW - 60_000).toISOString()
      const live = { ...activeRunBase, updatedAt: staleTime }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isStale).toBe(false)
    })

    it('updatedAt 30초 전 → isStale=false', () => {
      const recentTime = new Date(NOW - 30_000).toISOString()
      const live = { ...activeRunBase, updatedAt: recentTime }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isStale).toBe(false)
    })

    it('completed=true (isActiveRun=false) → isStale=false (실행 중 아님)', () => {
      const staleTime = new Date(NOW - 120_000).toISOString()
      const live = { ...activeRunBase, completed: true, updatedAt: staleTime }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isStale).toBe(false)
    })

    it('updatedAt=빈 문자열 → isStale=false (updatedAt 없는 경우)', () => {
      const live = { ...activeRunBase, updatedAt: '' }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isStale).toBe(false)
    })

    it('커스텀 staleThresholdMs=30_000 시 30초 초과하면 Stale', () => {
      const staleTime = new Date(NOW - 31_000).toISOString()
      const live = { ...activeRunBase, updatedAt: staleTime }
      const flags = computePipelineStateFlags(live, NOW, 30_000)
      expect(flags.isStale).toBe(true)
    })
  })

  // ── Mock 상태 (연결 없음) ──────────────────────────────────────────────────
  describe('Mock 상태 (연결 없음)', () => {
    it('connected=false → 모든 플래그 false', () => {
      const live = {
        connected: false,
        completed: false,
        steps: [],
        viewingArchive: null,
        updatedAt: '',
      }
      const flags = computePipelineStateFlags(live, NOW)
      expect(flags.isActiveRun).toBe(false)
      expect(flags.isArchive).toBe(false)
      expect(flags.isCompletedSnapshot).toBe(false)
      expect(flags.isStale).toBe(false)
    })
  })
})
