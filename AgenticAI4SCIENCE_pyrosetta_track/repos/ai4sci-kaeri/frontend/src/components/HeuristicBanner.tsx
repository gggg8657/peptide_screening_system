import { AlertTriangle, CheckCircle2, FlaskConical, ShieldAlert } from 'lucide-react'
import { cn } from '../lib/utils'

/**
 * HeuristicBanner — GATE-F 필수 컴포넌트
 *
 * 데이터 신뢰도 등급을 사용자에게 명확히 고지.
 * HL score / stability ranking 등 heuristic 계산값을 표시하는
 * 모든 UI 영역 상단에 의무적으로 배치해야 함.
 *
 * 등급 정의:
 *   A — 실측 기반 (in-vitro / in-vivo 검증 완료)
 *   B — in-silico 추정 (구조 기반, 실험 미수행)
 *   C — 검증 부족 (iPTM ≠ Ki, 순위 일치 낮음)
 *   HEURISTIC — ranking 전용 heuristic score, 절대값 아님
 */
export type HeuristicGrade = 'A' | 'B' | 'C' | 'HEURISTIC'

export interface HeuristicBannerProps {
  grade: HeuristicGrade
  warnings?: string[]
  compact?: boolean
  className?: string
}

const GRADE_CONFIG: Record<
  HeuristicGrade,
  {
    borderColor: string
    bgColor: string
    textColor: string
    labelColor: string
    label: string
    Icon: React.FC<{ className?: string }>
  }
> = {
  A: {
    borderColor: 'border-[var(--pos)]/30',
    bgColor: 'bg-[var(--pos-soft)]',
    textColor: 'text-[var(--pos)]',
    labelColor: 'text-[var(--pos)]',
    label: 'A — 실측 기반',
    Icon: ({ className }) => <CheckCircle2 className={className} />,
  },
  B: {
    borderColor: 'border-[var(--warn)]/30',
    bgColor: 'bg-[var(--warn-soft)]',
    textColor: 'text-[var(--warn)]',
    labelColor: 'text-[var(--warn)]',
    label: 'B — in-silico 추정',
    Icon: ({ className }) => <FlaskConical className={className} />,
  },
  C: {
    borderColor: 'border-[var(--warn)]/30',
    bgColor: 'bg-orange-900/20',
    textColor: 'text-[var(--warn)]',
    labelColor: 'text-[var(--warn)]',
    label: 'C — 검증 부족, 해석 주의',
    Icon: ({ className }) => <AlertTriangle className={className} />,
  },
  HEURISTIC: {
    borderColor: 'border-[var(--neg)]/30',
    bgColor: 'bg-[var(--neg-soft)]',
    textColor: 'text-[var(--neg)]',
    labelColor: 'text-[var(--neg)]',
    label: 'HEURISTIC — ranking 전용',
    Icon: ({ className }) => <ShieldAlert className={className} />,
  },
}

export function HeuristicBanner({
  grade,
  warnings = [],
  compact = false,
  className,
}: HeuristicBannerProps) {
  const cfg = GRADE_CONFIG[grade]
  const { Icon } = cfg

  return (
    <div
      role="note"
      aria-label={`데이터 신뢰도 등급: ${cfg.label}`}
      className={cn(
        'rounded-lg border-l-4 px-3 py-2.5',
        cfg.borderColor,
        cfg.bgColor,
        className,
      )}
    >
      <div className="flex items-center gap-2">
        <Icon className={cn('h-4 w-4 flex-shrink-0', cfg.labelColor)} />
        <span className={cn('text-xs font-semibold', cfg.labelColor)}>
          {cfg.label}
        </span>
      </div>

      {!compact && warnings.length > 0 && (
        <ul
          aria-label="신뢰도 경고 목록"
          className={cn('mt-1.5 space-y-0.5 pl-6', cfg.textColor)}
        >
          {warnings.map((w, i) => (
            <li key={i} className="text-[10px] leading-relaxed">
              • {w}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
