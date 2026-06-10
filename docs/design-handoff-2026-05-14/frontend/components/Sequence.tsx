/**
 * Sequence — 펩타이드 서열 시각화.
 *
 * 위치: src/components/Sequence.tsx
 *
 * - wildtype 대비 변이 위치 highlight
 * - Cys (C) 노랑 — SS bond
 * - FWKT pharmacophore (pos 6-9) 보라
 */

interface Props {
  seq: string;
  wildtype?: string;
  showRuler?: boolean;
  big?: boolean;
}

export function Sequence({
  seq,
  wildtype = 'AGCKNFFWKTFTSC',
  showRuler = false,
  big = false,
}: Props) {
  const aa = seq.split('');
  const wt = wildtype.split('');
  const cellSize = big ? 26 : 18;
  const cellHeight = big ? 30 : 22;

  return (
    <div className="inline-flex flex-col">
      {showRuler && (
        <div className="flex mb-0.5">
          {aa.map((_, i) => (
            <div
              key={i}
              className="text-center font-mono text-text-dim"
              style={{ width: cellSize, fontSize: 9 }}
            >
              {i + 1}
            </div>
          ))}
        </div>
      )}
      <div className="flex border border-border-base rounded overflow-hidden">
        {aa.map((c, i) => {
          const isMut = wt[i] && wt[i] !== c;
          const isCys = c === 'C';
          const isPharm = i >= 5 && i <= 8;

          let className = 'font-mono text-center border-r border-border-base last:border-r-0';
          if (isMut) className += ' bg-accent-soft text-accent font-bold';
          else if (isCys) className += ' text-warn font-bold';
          else if (isPharm) className += ' bg-violet-soft text-violet';

          return (
            <div
              key={i}
              className={className}
              style={{
                width: cellSize,
                height: cellHeight,
                lineHeight: `${cellHeight}px`,
                fontSize: big ? 14 : 12,
              }}
              title={`pos ${i + 1}: ${c}${isMut ? ` (WT: ${wt[i]})` : ''}`}
            >
              {c}
            </div>
          );
        })}
      </div>
    </div>
  );
}
