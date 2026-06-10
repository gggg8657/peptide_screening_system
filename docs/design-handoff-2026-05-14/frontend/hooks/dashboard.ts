/**
 * Data hooks · SSTR2 Dashboard
 *
 * 위치: src/hooks/dashboard.ts (또는 hooks/use*.ts 로 분리)
 *
 * 의존:
 *   @tanstack/react-query
 *   zustand (theme store)
 *
 * 백엔드: http://127.0.0.1:8787/api/* — vite.config.ts proxy 권장
 */

import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// ─────────────────────────────────────────────────────────────────────────────
// Types — see API_CONTRACT.md for full shapes

export type Silo = 'A' | 'B' | 'A+B';
export type Tier = 'T0' | 'T1' | 'T2' | 'T3';
export type StageStatus = 'queued' | 'running' | 'done' | 'failed';
export type WetlabStage = 'draft' | 'review' | 'approval' | 'PO' | 'shipped';

export interface RunStatus {
  run_id: string;
  started_at: string;
  duration_seconds: number;
  iteration: number;
  max_iterations: number;
  silo: Silo;
  llm_model: string;
  gpus: string;
  seed: number;
  current_step: string;
  progress: number;
  state: 'running' | 'done' | 'failed' | 'queued';
}

export interface Candidate {
  id: string;
  seq: string;
  tier: Tier;
  margin: number;
  best_receptor: string;
  iptm: Record<string, number>;
  ddg: number | null;
  source: string | null;
  mutations: string[];
  recommended: boolean;
  wildtype: boolean;
  notes: string | null;
}

export interface PipelineStage {
  id: string;
  name: string;
  group: 'input' | 'gen' | 'filter' | 'score' | 'refine' | 'analyze';
  tool: string;
  env: string | null;
  status: StageStatus;
  in_count: number | null;
  out_count: number | null;
  in_unit: string | null;
  out_unit: string | null;
  time: string | null;
  gpu: string | null;
  gate: string | null;
  pass?: number | null;
  fail?: number | null;
  progress: number | null;
}

export interface AgentEntry {
  ts: string;
  agent: 'planner' | 'builder' | 'qcranker' | 'diversity' | 'critic' | 'reporter';
  level: 'info' | 'warn' | 'error';
  text: string;
}

// ─────────────────────────────────────────────────────────────────────────────
const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Run status — polled

export function useRunStatus(runId: string | undefined) {
  return useQuery<RunStatus>({
    queryKey: ['status', runId],
    queryFn: () => get<RunStatus>(`/status?run_id=${runId}`),
    enabled: !!runId,
    refetchInterval: (q) => (q.state.data?.state === 'running' ? 5000 : false),
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Candidates

export function useCandidates(runId: string | undefined) {
  return useQuery<{ run_id: string; wild_type: string; candidates: Candidate[] }>({
    queryKey: ['candidates', runId],
    queryFn: () => get(`/experiment/${runId}/candidates`),
    enabled: !!runId,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Pipeline (per silo)

export function usePipeline(silo: Silo, runId?: string) {
  const siloKey = silo === 'A+B' ? 'Combined' : silo;
  const qs = runId ? `?run_id=${runId}` : '';
  return useQuery({
    queryKey: ['pipeline', siloKey, runId],
    queryFn: () => get(`/pipelines/${siloKey}${qs}`),
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Selectivity matrix

export function useSelectivity(runId: string | undefined) {
  return useQuery({
    queryKey: ['selectivity', runId],
    queryFn: () => get(`/selectivity/${runId}`),
    enabled: !!runId,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Agent log + SSE stream

export function useAgentLog(runId: string | undefined) {
  const [entries, setEntries] = useState<AgentEntry[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;

    // 1. Initial fetch
    get<{ entries: AgentEntry[] }>(`/agents/${runId}/log`).then((d) => {
      if (!cancelled) setEntries(d.entries ?? []);
    });

    // 2. SSE stream
    const es = new EventSource(`${BASE}/agents/${runId}/stream`);
    es.addEventListener('agent', (e: MessageEvent) => {
      if (cancelled) return;
      const entry = JSON.parse(e.data) as AgentEntry;
      setEntries((prev) => [...prev, entry]);
    });
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    return () => {
      cancelled = true;
      es.close();
    };
  }, [runId]);

  return { entries, connected };
}

// ─────────────────────────────────────────────────────────────────────────────
// cand03 variants

export function useCand03Variants() {
  return useQuery({
    queryKey: ['cand03_variants'],
    queryFn: () => get('/cand03_variants/list'),
    staleTime: 60_000,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// ADMET

export function useADMET(seqId: string | undefined) {
  return useQuery({
    queryKey: ['admet', seqId],
    queryFn: () => get(`/admet/${seqId}`),
    enabled: !!seqId,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Settings (gate thresholds)

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => get('/settings'),
    staleTime: 30_000,
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: object) =>
      fetch(`${BASE}/settings`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      }).then((r) => r.json()),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Run launcher

export interface RunStartRequest {
  name: string;
  silo: Silo;
  iterations: number;
  seed: number;
  n_backbone: number;
  k_seq_per_backbone: number;
  top_m_rosetta: number;
  llm_model: string;
  mutation_strategy: 'ga_bo' | 'enumerate' | 'sampling';
  off_targets: string[];
  boltz_cross_enabled: boolean;
  gates?: Record<string, number>;
}

export function useStartRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: RunStartRequest) => post('/runs/start', req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['status'] }),
  });
}

export function usePredictedPassRates(runId: string | undefined) {
  return useQuery({
    queryKey: ['predicted', runId],
    queryFn: () => get(`/runs/${runId}/predicted_pass_rates`),
    enabled: !!runId,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Benchmark

export function useBenchmark(phase: 'Phase1' | 'Phase2' | 'Phase3' | 'V2' = 'V2') {
  return useQuery({
    queryKey: ['benchmark', phase],
    queryFn: () => get(`/benchmark/results?phase=${phase}`),
    staleTime: 5 * 60_000,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Wetlab

export function useWetlabOrders() {
  return useQuery({
    queryKey: ['wetlab_orders'],
    queryFn: () => get('/wetlab/orders'),
  });
}

export function useWetlabOrder(orderId: string | undefined) {
  return useQuery({
    queryKey: ['wetlab_order', orderId],
    queryFn: () => get(`/wetlab/orders/${orderId}`),
    enabled: !!orderId,
  });
}

export function useTransitionWetlabOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, to_stage, note }: { orderId: string; to_stage: WetlabStage; note?: string }) =>
      post(`/wetlab/orders/${orderId}/transition`, { to_stage, note }),
    onSuccess: (_data, { orderId }) => {
      qc.invalidateQueries({ queryKey: ['wetlab_order', orderId] });
      qc.invalidateQueries({ queryKey: ['wetlab_orders'] });
    },
  });
}
