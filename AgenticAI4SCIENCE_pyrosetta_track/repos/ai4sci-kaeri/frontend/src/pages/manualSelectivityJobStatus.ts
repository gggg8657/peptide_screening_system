import type { LucideIcon } from 'lucide-react'
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2,
  XCircle,
} from 'lucide-react'
import type { FlexPepDockJobSummary } from '../hooks/useFlexPepDockJob'

export type ClassifiedJobStatus = {
  label: string
  /** 아이콘/포그라운드용 디자인 토큰 (OKLCH CSS 변수) */
  color: string
  Icon: LucideIcon
  /** Loader2 회전 여부 */
  spinIcon: boolean
  badgeClassName: string
}

function normalizedMessage(job: Pick<FlexPepDockJobSummary, 'error_message'>): string {
  return (job.error_message ?? '').toLowerCase()
}

/**
 * Manual Selectivity 잡 상태를 사용자 라벨·색·아이콘으로 분류한다.
 * failed 시 error_message 로 timeout / 사용자 취소 / 기타 오류를 구분한다.
 */
export function classifyJobStatus(
  job: Pick<FlexPepDockJobSummary, 'status' | 'error_message'>,
): ClassifiedJobStatus {
  const { status } = job
  const err = normalizedMessage(job)

  if (status === 'queued') {
    return {
      label: '큐 대기',
      color: 'var(--text-mute)',
      Icon: Clock,
      spinIcon: false,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-bg-sunk px-2 py-1 text-[11px] font-semibold text-[color:var(--text-mute)]',
    }
  }

  if (status === 'running') {
    return {
      label: '진행 중',
      color: 'var(--accent)',
      Icon: Loader2,
      spinIcon: true,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-2 py-1 text-[11px] font-semibold text-[color:var(--accent)]',
    }
  }

  if (status === 'done') {
    return {
      label: '완료',
      color: 'var(--pos)',
      Icon: CheckCircle,
      spinIcon: false,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-[var(--pos-soft)] px-2 py-1 text-[11px] font-semibold text-[color:var(--pos)]',
    }
  }

  if (status === 'cancelling') {
    return {
      label: '취소 중',
      color: 'var(--warn)',
      Icon: Loader2,
      spinIcon: true,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-[var(--warn-soft)] px-2 py-1 text-[11px] font-semibold text-[color:var(--warn)]',
    }
  }

  if (status === 'cancelled') {
    return {
      label: '사용자 취소',
      color: 'var(--text-mute)',
      Icon: XCircle,
      spinIcon: false,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-bg-sunk px-2 py-1 text-[11px] font-semibold text-[color:var(--text-mute)]',
    }
  }

  if (status === 'failed') {
    if (err.includes('timeout')) {
      return {
        label: '시간 초과로 종료',
        color: 'var(--warn)',
        Icon: AlertTriangle,
        spinIcon: false,
        badgeClassName:
          'inline-flex items-center gap-1 rounded-full bg-[var(--warn-soft)] px-2 py-1 text-[11px] font-semibold text-[color:var(--warn)]',
      }
    }
    if (err.includes('사용자 취소')) {
      return {
        label: '사용자 취소',
        color: 'var(--text-mute)',
        Icon: XCircle,
        spinIcon: false,
        badgeClassName:
          'inline-flex items-center gap-1 rounded-full bg-bg-sunk px-2 py-1 text-[11px] font-semibold text-[color:var(--text-mute)]',
      }
    }
    return {
      label: '오류',
      color: 'var(--neg)',
      Icon: AlertOctagon,
      spinIcon: false,
      badgeClassName:
        'inline-flex items-center gap-1 rounded-full bg-[var(--neg-soft)] px-2 py-1 text-[11px] font-semibold text-[color:var(--neg)]',
    }
  }

  return {
    label: status,
    color: 'var(--text-mute)',
    Icon: Clock,
    spinIcon: false,
    badgeClassName:
      'inline-flex items-center gap-1 rounded-full bg-bg-sunk px-2 py-1 text-[11px] font-semibold text-text-mute',
  }
}
