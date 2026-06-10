import { describe, expect, it } from 'vitest'
import { AlertOctagon, AlertTriangle, XCircle } from 'lucide-react'
import { classifyJobStatus } from '../manualSelectivityJobStatus'

describe('classifyJobStatus (failed / error_message)', () => {
  it('error_message에 timeout이 포함되면 시간 초과·주황(warn)·AlertTriangle으로 분류한다', () => {
    const c = classifyJobStatus({
      status: 'failed',
      error_message: 'Job TIMEOUT after 6h',
    })
    expect(c.label).toBe('시간 초과로 종료')
    expect(c.color).toBe('var(--warn)')
    expect(c.Icon).toBe(AlertTriangle)
    expect(c.spinIcon).toBe(false)
  })

  it('error_message에 사용자 취소가 포함되면 회색(mute)·XCircle으로 분류한다', () => {
    const c = classifyJobStatus({
      status: 'failed',
      error_message: '사용자 취소에 의해 중단됨',
    })
    expect(c.label).toBe('사용자 취소')
    expect(c.color).toBe('var(--text-mute)')
    expect(c.Icon).toBe(XCircle)
    expect(c.spinIcon).toBe(false)
  })

  it('failed 이지만 timeout/사용자 취소가 아니면 일반 오류·빨강(neg)·AlertOctagon으로 분류한다', () => {
    const c = classifyJobStatus({
      status: 'failed',
      error_message: 'Rosetta crashed with exit code 1',
    })
    expect(c.label).toBe('오류')
    expect(c.color).toBe('var(--neg)')
    expect(c.Icon).toBe(AlertOctagon)
    expect(c.spinIcon).toBe(false)
  })
})
