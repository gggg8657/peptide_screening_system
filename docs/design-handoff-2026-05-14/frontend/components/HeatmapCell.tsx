/**
 * HeatmapCell — iPTM 값 히트맵 셀.
 *
 * 위치: src/components/HeatmapCell.tsx
 *
 * - 값 0.75–1.0 범위를 cool → hot 으로 매핑
 * - best receptor: 진한 outline
 * - target SSTR2: 점선 outline
 * - selected: accent border
 */

import clsx from 'clsx';

interface Props {
  value: number;
  isBest?: boolean;
  isTarget?: boolean;
  selected?: boolean;
  onClick?: () => void;
  size?: number;
}

export function iptmColor(v: number): string {
  // 0.75 → cool stone, 0.98 → hot accent
  const t = Math.max(0, Math.min(1, (v - 0.75) / 0.25));
  if (t < 0.33) return `oklch(0.92 0.04 220 / ${0.4 + t})`;
  if (t < 0.66) return `oklch(0.82 0.10 200 / ${0.5 + t * 0.4})`;
  return `oklch(0.7 0.14 195 / ${0.65 + t * 0.35})`;
}

export function HeatmapCell({ value, isBest, isTarget, selected, onClick, size }: Props) {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'aspect-square w-full flex items-center justify-center rounded-sm font-mono text-[11px] cursor-pointer transition-transform',
        'hover:scale-[1.02]',
        selected
          ? 'border-2 border-accent'
          : isBest
            ? 'border border-text-base'
            : 'border border-border-base',
        value > 0.92 ? 'text-white' : 'text-text-base',
        isBest && 'font-bold',
      )}
      style={{
        background: iptmColor(value),
        ...(isTarget && {
          outline: '1.5px dashed var(--accent)',
          outlineOffset: -3,
        }),
        ...(size && { width: size, height: size }),
      }}
      title={`iPTM ${value.toFixed(3)}`}
    >
      {value.toFixed(2).slice(1)}
    </div>
  );
}
