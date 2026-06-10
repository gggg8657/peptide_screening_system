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
  label?: string;
  title?: string;
}

// eslint-disable-next-line react-refresh/only-export-components
export function iptmColor(v: number): string {
  // 0.75 → cool stone, 0.98 → hot accent
  // 라이트 모드에서는 더 진한 색 사용 (배경 #fafaf9 lightness ~0.99에서 가시성 확보).
  // 다크 모드는 CSS @media 또는 [data-theme="dark"] 에서 override되지만, oklch lightness가
  // 0.50~0.78 범위라 다크 배경(#0c0a09 ~0.10)에서도 충분히 보임.
  const t = Math.max(0, Math.min(1, (v - 0.75) / 0.25));
  if (t < 0.33) return `oklch(0.72 0.06 220 / ${0.55 + t})`;
  if (t < 0.66) return `oklch(0.58 0.12 200 / ${0.7 + t * 0.3})`;
  return `oklch(0.47 0.16 195 / ${0.85 + t * 0.15})`;
}

export function HeatmapCell({ value, isBest, isTarget, selected, onClick, size, label, title }: Props) {
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
        'text-white',
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
      title={title ?? `iPTM ${value.toFixed(3)}`}
    >
      {label ?? value.toFixed(2).slice(1)}
    </div>
  );
}
