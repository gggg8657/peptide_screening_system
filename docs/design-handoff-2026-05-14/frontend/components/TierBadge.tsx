/**
 * TierBadge — T0 / T1 / T2 / T3 selectivity tier 표시.
 *
 * 위치: src/components/TierBadge.tsx
 */

import clsx from 'clsx';

interface Props {
  tier: 'T0' | 'T1' | 'T2' | 'T3';
  className?: string;
}

const TIER_STYLES = {
  T0: 'bg-neg-soft text-neg',
  T1: 'bg-warn-soft text-warn',
  T2: 'bg-pos-soft text-pos',
  T3: 'bg-accent-soft text-accent',
} as const;

export function TierBadge({ tier, className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-1.5 py-0 rounded text-[10.5px] font-semibold font-mono tracking-wide',
        TIER_STYLES[tier],
        className,
      )}
    >
      {tier}
    </span>
  );
}
