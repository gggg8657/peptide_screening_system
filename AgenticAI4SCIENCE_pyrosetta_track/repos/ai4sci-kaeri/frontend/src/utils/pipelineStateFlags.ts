/**
 * P04: isLive 4-상태 분리 유틸리티
 *
 * App.tsx에서 인라인으로 계산하던 isLive 단일 boolean을
 * 4가지 상호 독립적 플래그로 분리한 순수 함수.
 * 테스트 가능하도록 PipelineStatus와 완전 분리.
 */

export interface PipelineStateFlags {
  /** 현재 실행 중인 run (connected=true, completed=false, steps>0) */
  isActiveRun: boolean
  /** 보관된 run을 조회 중 */
  isArchive: boolean
  /** 완료된 run 결과 스냅샷 (connected=true, completed=true, archive 아님) */
  isCompletedSnapshot: boolean
  /**
   * 갱신 지연 — isActiveRun이지만 updatedAt이 60초 이상 경과.
   * 표시 우선순위: Stale > Archive > Active > Completed > Mock
   */
  isStale: boolean
}

export interface PipelineStateFlagsInput {
  connected: boolean
  completed: boolean
  steps: unknown[]
  viewingArchive: string | null
  updatedAt: string
}

/**
 * @param live  usePipelineStatus 반환값의 서브셋
 * @param now   현재 타임스탬프 (ms). 기본값 Date.now(). 테스트 시 고정 가능.
 * @param staleThresholdMs  Stale 임계값 (기본 60_000ms)
 */
export function computePipelineStateFlags(
  live: PipelineStateFlagsInput,
  now: number = Date.now(),
  staleThresholdMs = 60_000,
): PipelineStateFlags {
  const isActiveRun = live.connected && !live.completed && live.steps.length > 0
  const isArchive = !!live.viewingArchive
  const isCompletedSnapshot = live.connected && live.completed && !isArchive
  const isStale =
    isActiveRun &&
    (live.updatedAt
      ? now - new Date(live.updatedAt).getTime() > staleThresholdMs
      : false)

  return { isActiveRun, isArchive, isCompletedSnapshot, isStale }
}
