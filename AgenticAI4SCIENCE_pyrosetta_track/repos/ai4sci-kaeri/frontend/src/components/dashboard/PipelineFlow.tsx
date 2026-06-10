/**
 * PipelineFlow — Silo별 파이프라인 진행 시각화.
 *
 * 위치: src/components/PipelineFlow.tsx
 *
 * Props:
 *   silo: "A" | "B" | "A+B"
 *   runId?: string — 실제 run 의 상태로 hydrate. 없으면 template 만 표시.
 *
 * Behavior:
 *   - silo 별로 다른 stage 배열 (A: Backbone/Sequence, B: Constraint/Mutation/Diversity, A+B: parallel tracks)
 *   - 각 stage 카드: status dot, ID + name, tool, in/out count, progress bar, gate
 *   - hover: 자세한 metadata
 *
 * 이 컴포넌트는 prototype/pipeline_flow.jsx 의 TSX 포팅 버전.
 */

import { Fragment } from 'react';
import clsx from 'clsx';
import { usePipeline, type PipelineStage, type PipelineTrack } from '../../hooks/dashboard';

interface Props {
  silo: 'A' | 'B' | 'A+B';
  runId?: string;
  onSelectStage?: (s: PipelineStage) => void;
  selectedStage?: string;
}

export function PipelineFlow({ silo, runId, onSelectStage, selectedStage }: Props) {
  const { data: pipeline, isLoading, error } = usePipeline(silo, runId);

  if (isLoading) return <div className="p-4 text-text-mute text-sm">파이프라인 로딩…</div>;
  if (error)     return <div className="p-4 text-neg text-sm">pipeline 로드 실패: {String(error)}</div>;
  if (!pipeline) return null;

  // Linear (A or B) vs Combined
  const isLinear = 'stages' in pipeline;
  const allStages: PipelineStage[] = isLinear
    ? pipeline.stages
    : [
        pipeline.input,
        ...(pipeline.tracks?.[0]?.stages ?? []),
        ...(pipeline.tracks?.[1]?.stages ?? []),
        ...(pipeline.converge ?? []),
      ];

  const doneN = allStages.filter((s) => s.status === 'done').length;
  const runningN = allStages.filter((s) => s.status === 'running').length;
  const queuedN = allStages.filter((s) => s.status === 'queued').length;
  const overall = (doneN + runningN * 0.5) / allStages.length;

  return (
    <div className="bg-bg-elev border border-border-base rounded overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-3 py-2 border-b border-border-base">
        <div className="flex items-center gap-2.5 text-[11px] font-semibold uppercase tracking-wider text-text-mute">
          <span>{pipeline.name}</span>
          <span className="font-normal normal-case tracking-normal text-text-dim">
            {pipeline.description}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <Pill tone="pos">done {doneN}</Pill>
          {runningN > 0 && <Pill tone="accent" dot>{runningN}</Pill>}
          <Pill>queued {queuedN}</Pill>
          <div className="w-20 h-1 bg-bg-sunk rounded overflow-hidden">
            <div className="h-full bg-accent transition-all" style={{ width: `${overall * 100}%` }} />
          </div>
          <span className="font-mono text-text-mute w-7 text-right">{Math.round(overall * 100)}%</span>
        </div>
      </header>

      {/* Body */}
      <div className="p-3">
        {isLinear ? (
          <LinearFlow stages={pipeline.stages} onSelectStage={onSelectStage} selectedStage={selectedStage} />
        ) : (
          <CombinedFlow
            input={pipeline.input}
            tracks={pipeline.tracks}
            converge={pipeline.converge}
            onSelectStage={onSelectStage}
            selectedStage={selectedStage}
          />
        )}
      </div>

      {/* Legend */}
      <footer className="flex flex-wrap gap-3 px-3 py-2 border-t border-border-base text-[10px] text-text-mute">
        {GROUPS.map(([k, label]) => (
          <span key={k} className="inline-flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ background: GROUP_COLORS[k].bg, border: `1px solid ${GROUP_COLORS[k].accent}` }} />
            {label}
          </span>
        ))}
      </footer>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function LinearFlow({ stages, onSelectStage, selectedStage }: {
  stages: PipelineStage[];
  onSelectStage?: (s: PipelineStage) => void;
  selectedStage?: string;
}) {
  return (
    <div className="flex items-stretch overflow-x-auto pb-1">
      {stages.map((s, i) => (
        <Fragment key={s.id + i}>
          <StageNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
          {i < stages.length - 1 && <Arrow active={s.status === 'done'} />}
        </Fragment>
      ))}
    </div>
  );
}

function CombinedFlow({ input, tracks, converge, onSelectStage, selectedStage }: {
  input: PipelineStage;
  tracks: PipelineTrack[];
  converge: PipelineStage[];
  onSelectStage?: (s: PipelineStage) => void;
  selectedStage?: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      {/* Shared input */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-text-dim w-20">shared</span>
        <StageNode stage={input} compact onClick={() => onSelectStage?.(input)} selected={selectedStage === input.id} />
        <span className="font-mono text-[10px] text-text-dim">fork →</span>
      </div>

      {/* Parallel tracks */}
      {tracks.map((track) => (
        <div key={track.silo} className="grid grid-cols-[80px_1fr] gap-2 items-center">
          <span className="text-[10px] uppercase tracking-wider" style={{ color: track.silo === 'A' ? 'var(--violet)' : 'var(--teal)' }}>
            silo {track.silo} · {track.label}
          </span>
          <div className="flex items-stretch overflow-x-auto">
            {track.stages.map((s: PipelineStage, i: number) => (
              <Fragment key={track.silo + s.id + i}>
                <StageNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
                {i < track.stages.length - 1 && <Arrow active={s.status === 'done'} />}
              </Fragment>
            ))}
          </div>
        </div>
      ))}

      <div className="pl-20 text-[10px] text-text-dim font-mono">→ converge: shared scoring · refine · analyze</div>

      {/* Converge */}
      <div className="grid grid-cols-[80px_1fr] gap-2 items-center">
        <span className="text-[10px] uppercase tracking-wider text-text-dim">shared</span>
        <div className="flex items-stretch overflow-x-auto">
          {converge.map((s, i) => (
            <Fragment key={'c' + s.id + i}>
              <StageNode stage={s} compact onClick={() => onSelectStage?.(s)} selected={selectedStage === s.id} />
              {i < converge.length - 1 && <Arrow active={s.status === 'done'} />}
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
function StageNode({ stage, compact, onClick, selected }: {
  stage: PipelineStage;
  compact?: boolean;
  onClick?: () => void;
  selected?: boolean;
}) {
  const g = GROUP_COLORS[stage.group] ?? GROUP_COLORS.input;
  const isRunning = stage.status === 'running';
  const isDone = stage.status === 'done';
  const isQueued = stage.status === 'queued';
  const passRate = stage.in_count && stage.out_count != null
    ? stage.out_count / stage.in_count : null;

  return (
    <div
      onClick={onClick}
      className={clsx(
        'relative bg-bg-elev rounded overflow-hidden',
        compact ? 'min-w-[130px] p-1.5 px-2' : 'min-w-[180px] p-2',
        onClick && 'cursor-pointer',
        isQueued && 'opacity-70',
      )}
      style={{
        border: `1px solid ${selected ? 'var(--accent)' : isRunning ? g.accent : 'var(--border)'}`,
      }}
    >
      {/* Top strip */}
      <div
        className="absolute top-0 left-0 right-0 h-0.5"
        style={{ background: isDone ? 'var(--pos)' : isRunning ? g.accent : 'var(--border)' }}
      />
      {isRunning && stage.progress != null && (
        <div
          className="absolute top-0 left-0 h-0.5 bg-accent"
          style={{ width: `${(stage.progress ?? 0.3) * 100}%`, boxShadow: '0 0 8px var(--accent)' }}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-1.5 mt-0.5">
        <StatusDot status={stage.status} />
        <span className="font-mono text-[10px] text-text-dim">{stage.id}</span>
        <span className={clsx('font-semibold', compact ? 'text-[11.5px]' : 'text-[12.5px]')}>{stage.name}</span>
      </div>
      <div className="text-[10px] text-text-mute mt-0.5 leading-tight min-h-[13px]">{stage.tool}</div>

      {/* I/O */}
      {!compact && (stage.in_count != null || stage.out_count != null) && (
        <div className="flex items-center gap-1 mt-1.5 text-[10px]">
          {stage.in_count != null && (
            <span className="font-mono text-text-mute">{stage.in_count}<span className="opacity-60 text-[9px]"> {stage.in_unit}</span></span>
          )}
          {stage.in_count != null && stage.out_count != null && <span className="text-text-dim">→</span>}
          {stage.out_count != null && (
            <span className="font-mono font-semibold" style={{ color: g.fg }}>
              {stage.out_count}<span className="opacity-60 text-[9px] font-normal"> {stage.out_unit}</span>
            </span>
          )}
        </div>
      )}

      {/* Progress / Pass-Fail */}
      {isRunning && stage.progress != null && (
        <div className="mt-1.5">
          <div className="h-[3px] bg-bg-sunk rounded-sm overflow-hidden">
            <div className="h-full" style={{ width: `${stage.progress * 100}%`, background: g.accent }} />
          </div>
          <div className="flex justify-between mt-0.5 text-[9px] font-mono text-text-mute">
            <span>{Math.round((stage.progress ?? 0) * 100)}%</span>
            <span>{stage.time}</span>
          </div>
        </div>
      )}

      {isDone && passRate != null && stage.in_count! > 0 && (
        <div className="mt-1.5">
          <div className="h-[3px] bg-neg-soft rounded-sm overflow-hidden flex">
            <div className="h-full bg-pos" style={{ width: `${passRate * 100}%` }} />
          </div>
          <div className="flex justify-between mt-0.5 text-[9px] font-mono">
            <span className="text-pos">pass {stage.out_count}</span>
            <span className="text-neg">fail {stage.in_count! - stage.out_count!}</span>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex gap-1 mt-1.5 flex-wrap items-center">
        {stage.gate && (
          <span
            className="font-mono text-[9px] px-1 py-0 rounded-sm font-medium"
            style={{ background: g.bg, color: g.fg }}
          >
            {stage.gate}
          </span>
        )}
        {!compact && isDone && stage.time && (
          <span className="font-mono text-[9px] text-text-dim ml-auto">{stage.time}</span>
        )}
        {!compact && stage.gpu && <span className="font-mono text-[9px] text-text-dim">{stage.gpu}</span>}
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: PipelineStage['status'] }) {
  if (status === 'done') {
    return (
      <span className="w-3.5 h-3.5 rounded-full bg-pos grid place-items-center">
        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </span>
    );
  }
  if (status === 'running') {
    return (
      <span className="relative w-3.5 h-3.5 rounded-full bg-accent">
        <span className="absolute inset-[-3px] rounded-full border-[1.5px] border-accent animate-pulse" />
      </span>
    );
  }
  if (status === 'failed') return <span className="w-3.5 h-3.5 rounded-full bg-neg" />;
  return <span className="w-3.5 h-3.5 rounded-full border-[1.5px] border-border-strong bg-bg-elev" />;
}

function Arrow({ active }: { active: boolean }) {
  return (
    <div className="w-[18px] flex items-center justify-center flex-shrink-0">
      <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
        <path
          d="M0 7h14M10 2l5 5-5 5"
          stroke={active ? 'var(--accent)' : 'var(--border-strong)'}
          strokeWidth="1.2"
        />
      </svg>
    </div>
  );
}

function Pill({ tone, dot, children }: {
  tone?: 'pos' | 'warn' | 'neg' | 'accent';
  dot?: boolean;
  children: React.ReactNode;
}) {
  const toneClass = tone === 'pos' ? 'bg-pos-soft text-pos'
    : tone === 'warn' ? 'bg-warn-soft text-warn'
    : tone === 'neg' ? 'bg-neg-soft text-neg'
    : tone === 'accent' ? 'bg-accent-soft text-accent-text'
    : 'bg-bg-sunk text-text-mute border border-border-strong';
  return (
    <span className={clsx('inline-flex items-center gap-1 px-1.5 py-0 rounded-sm font-mono text-[9.5px] font-medium', toneClass)}>
      {dot && <span className="w-1 h-1 rounded-full bg-current animate-pulse" />}
      {children}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
const GROUP_COLORS = {
  input:   { bg: 'var(--bg-sunk)',     fg: 'var(--text-mute)',  accent: 'var(--text-mute)' },
  gen:     { bg: 'var(--violet-soft)', fg: 'var(--violet)',     accent: 'var(--violet)' },
  filter:  { bg: 'var(--teal-soft)',   fg: 'var(--teal)',       accent: 'var(--teal)' },
  score:   { bg: 'var(--accent-soft)', fg: 'var(--accent-text)',accent: 'var(--accent)' },
  refine:  { bg: 'var(--warn-soft)',   fg: 'var(--warn)',       accent: 'var(--warn)' },
  analyze: { bg: 'var(--bg-sunk)',     fg: 'var(--text-mute)',  accent: 'var(--text-mute)' },
} as const;

const GROUPS: [keyof typeof GROUP_COLORS, string][] = [
  ['input', 'input'],
  ['gen', 'generation'],
  ['filter', 'filter'],
  ['score', 'score'],
  ['refine', 'refine'],
  ['analyze', 'analyze'],
];
