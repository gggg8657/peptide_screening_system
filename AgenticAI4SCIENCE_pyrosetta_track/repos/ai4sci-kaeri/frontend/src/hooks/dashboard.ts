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
export type WetlabStage = 'draft' | 'submitted' | 'approved' | 'shipped' | 'returned';

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

export interface RunSummary {
  run_id: string;
  started_at: string;
  completed: boolean;
  n_candidates: number;
  best_ddg: number | null;
  label?: string;
  llm_model?: string;
}

export interface RunsResponse {
  runs: RunSummary[];
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

export interface SelectivityEntry {
  seq?: string;
  iptm: Record<string, number>;
  margin: number;
  tier: Tier;
  best_receptor: string;
  poseUrl?: string;
  source?: string | null;
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

export interface PipelineTrack {
  silo: 'A' | 'B';
  label: string;
  stages: PipelineStage[];
}

export interface PipelineLinear {
  name: string;
  description?: string;
  stages: PipelineStage[];
}

export interface PipelineCombined {
  name: string;
  description?: string;
  input: PipelineStage;
  tracks: PipelineTrack[];
  converge: PipelineStage[];
}

export type PipelineResponse = PipelineLinear | PipelineCombined;

export interface AgentEntry {
  ts: string;
  agent: 'planner' | 'builder' | 'qcranker' | 'diversity' | 'critic' | 'reporter';
  level: 'info' | 'warn' | 'error';
  text: string;
}

export interface BenchmarkLLMSpec {
  id: string;
  short: string;
  vram_gb: number;
}

export interface BenchmarkFlowSpec {
  id: 'sequential' | 'collaborative' | 'hierarchical';
  name: string;
  desc: string;
}

export interface BenchmarkCell {
  pass_rate: number;
  time_min: number;
  candidates: number;
  t2: number;
  cost: number;
}

export interface BenchmarkResponse {
  phase: 'Phase1' | 'Phase2' | 'Phase3' | 'V2';
  total_runs: number;
  llms: BenchmarkLLMSpec[];
  flows: BenchmarkFlowSpec[];
  matrix: Record<string, Record<string, BenchmarkCell>>;
}

export interface WetlabOrderListItem {
  id: string;
  candidate_id: string;
  stage: WetlabStage;
  total_krw: number;
  lead_weeks: number;
  requested_by: string;
  created_at: string;
}

export interface WetlabOrderListResponse {
  orders: WetlabOrderListItem[];
}

export interface WetlabPredictedKi {
  receptor: string;
  iptm: number;
  sst14_ki_nm: number | null;
  predicted_ki: string;
  target: boolean;
}

export interface WetlabReagent {
  name: string;
  spec: string;
  vendor: string;
  unit_price_krw: number;
  qty: number;
  lead_days: string;
}

export interface WetlabProtocol {
  format: string;
  tracer: string;
  membrane: string;
  concentration_range: string;
  replicates: string;
  negative_control: string;
  readout: string;
  analysis: string;
}

export interface WetlabAcceptanceCriterion {
  criterion: string;
  passed: boolean | null;
}

export interface WetlabTimelineEntry {
  week: string;
  task: string;
  actor: string;
}

export interface WetlabOrder {
  id: string;
  candidate_id: string;
  candidate_seq: string;
  stage: WetlabStage;
  total_krw: number;
  lead_weeks: number;
  requested_by: string;
  created_at: string;
  hypothesis: Record<string, string>;
  predicted_ki: WetlabPredictedKi[];
  reagents: WetlabReagent[];
  protocol: WetlabProtocol;
  acceptance_criteria: WetlabAcceptanceCriterion[];
  timeline: WetlabTimelineEntry[];
}

export interface CreateWetlabOrderRequest {
  candidate_id: string;
  flexpepdock_job_id?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
const BASE = '/api';
const RECEPTORS = ['SSTR1', 'SSTR2', 'SSTR3', 'SSTR4', 'SSTR5'] as const;
const DEFAULT_WILD_TYPE = 'AGCKNFFWKTFTSC';

type RunPayload = Record<string, unknown>;

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function getOptional<T>(path: string): Promise<T | null> {
  const res = await fetch(`${BASE}${path}`);
  if (res.status === 404) return null;
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

function numberValue(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function stringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function normalizeProgress(value: unknown): number {
  const progress = numberValue(value, 0);
  if (progress <= 0) return 0;
  if (progress <= 1) return progress;
  return Math.min(progress / 100, 1);
}

function normalizeTier(value: unknown, margin: number): Tier {
  if (value === 'T0' || value === 'T1' || value === 'T2' || value === 'T3') {
    return value;
  }
  if (typeof value === 'number') {
    if (value >= 3) return 'T2';
    if (value >= 2) return 'T1';
    return 'T0';
  }
  if (margin > 0) return 'T2';
  if (margin > -0.05) return 'T1';
  return 'T0';
}

function normalizeIptm(raw: unknown): Record<string, number> {
  const source = raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
  const iptm: Record<string, number> = {};
  for (const receptor of RECEPTORS) {
    iptm[receptor] = numberValue(source[receptor], 0);
  }
  return iptm;
}

function computeMargin(iptm: Record<string, number>, fallback: unknown): number {
  if (typeof fallback === 'number' && Number.isFinite(fallback)) return fallback;
  const offTargets = RECEPTORS.filter((receptor) => receptor !== 'SSTR2');
  const offTargetMax = Math.max(...offTargets.map((receptor) => iptm[receptor] ?? 0), 0);
  return numberValue(iptm.SSTR2, 0) - offTargetMax;
}

function findBestReceptor(iptm: Record<string, number>, fallback: unknown): string {
  if (typeof fallback === 'string' && fallback) return fallback;
  return RECEPTORS.reduce(
    (best, receptor) => ((iptm[receptor] ?? 0) > (iptm[best] ?? 0) ? receptor : best),
    'SSTR2',
  );
}

function computeMutations(sequence: string, wildType: string): string[] {
  if (!sequence || !wildType || sequence.length !== wildType.length) return [];
  const mutations: string[] = [];
  for (let index = 0; index < sequence.length; index += 1) {
    if (sequence[index] !== wildType[index]) {
      mutations.push(`${wildType[index]}${index + 1}→${sequence[index]}`);
    }
  }
  return mutations;
}

function readWildType(payload: RunPayload): string {
  const baseline = payload.baseline;
  if (baseline && typeof baseline === 'object') {
    const baselineSequence = stringValue((baseline as Record<string, unknown>).sequence);
    if (baselineSequence) return baselineSequence;
  }
  const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
  const baselineCandidate = candidates.find((candidate) => {
    if (!candidate || typeof candidate !== 'object') return false;
    const entry = candidate as Record<string, unknown>;
    return (
      entry.wildtype === true
      || stringValue(entry.id).toLowerCase().includes('baseline')
      || stringValue(entry.result) === 'REF'
    );
  });
  if (baselineCandidate && typeof baselineCandidate === 'object') {
    const sequence = stringValue((baselineCandidate as Record<string, unknown>).sequence);
    if (sequence) return sequence;
  }
  return DEFAULT_WILD_TYPE;
}

async function fetchRunPayload(runId: string | undefined): Promise<RunPayload> {
  if (runId) {
    const archived = await getOptional<RunPayload>(`/runs/${runId}`);
    if (archived) return archived;
  }
  const live = await get<RunPayload>('/status');
  if (!runId || stringValue(live.run_id) === runId) return live;
  throw new Error(`Run ${runId} not found`);
}

function adaptRunStatus(payload: RunPayload): RunStatus {
  const completed = payload.completed === true;
  const running = payload.is_active_run === true || payload.connected === true;
  return {
    run_id: stringValue(payload.run_id),
    started_at: stringValue(payload.started_at),
    duration_seconds: numberValue(payload.duration_seconds),
    iteration: numberValue(payload.iteration),
    max_iterations: numberValue(payload.total_iterations ?? payload.max_iterations),
    silo: payload.silo === 'A' || payload.silo === 'B' || payload.silo === 'A+B' ? payload.silo : 'B',
    llm_model: stringValue(payload.llm_model),
    gpus: stringValue(payload.gpus),
    seed: numberValue(payload.seed),
    current_step: stringValue(payload.current_step || payload.phase),
    progress: normalizeProgress(payload.progress),
    state: completed ? 'done' : running ? 'running' : 'queued',
  };
}

function adaptCandidate(raw: unknown, wildType: string): Candidate {
  const entry = raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
  const seq = stringValue(entry.sequence || entry.seq);
  const iptm = normalizeIptm(entry.iptm ?? entry.iptms);
  const margin = computeMargin(iptm, entry.selectivity_margin ?? entry.margin);
  const mutations = Array.isArray(entry.mutations)
    ? entry.mutations.filter((mutation): mutation is string => typeof mutation === 'string')
    : computeMutations(seq, wildType);
  const source = stringValue(entry.source || entry.pdb_path || entry.run_id) || null;
  const wildtype = entry.wildtype === true || stringValue(entry.id).toLowerCase().includes('baseline') || seq === wildType;

  return {
    id: stringValue(entry.id || entry.candidate_id),
    seq,
    tier: normalizeTier(entry.tier, margin),
    margin,
    best_receptor: findBestReceptor(iptm, entry.best_receptor),
    iptm,
    ddg: typeof entry.ddG === 'number' ? entry.ddG : typeof entry.ddg === 'number' ? entry.ddg : null,
    source,
    mutations,
    recommended: entry.recommended === true || margin > 0,
    wildtype,
    notes: stringValue(entry.notes || entry.failReason) || null,
  };
}

function adaptCandidatesPayload(payload: RunPayload) {
  const wildType = readWildType(payload);
  const candidates = Array.isArray(payload.candidates) ? payload.candidates.map((candidate) => adaptCandidate(candidate, wildType)) : [];
  return {
    run_id: stringValue(payload.run_id),
    wild_type: wildType,
    candidates,
  };
}

function adaptSelectivityEntry(raw: unknown): Partial<Candidate> & { poseUrl?: string } {
  const entry = raw && typeof raw === 'object' ? raw as Record<string, unknown> : {};
  const iptm = normalizeIptm(entry.iptm ?? entry.iptms);
  const margin = computeMargin(iptm, entry.selectivity_margin ?? entry.margin ?? entry.wsm);
  return {
    id: stringValue(entry.id || entry.candidate_id || entry.seq_id),
    seq: stringValue(entry.seq || entry.sequence),
    tier: normalizeTier(entry.tier, margin),
    margin,
    best_receptor: findBestReceptor(iptm, entry.best_receptor),
    iptm,
  };
}

async function fetchSelectivityPayload(runId: string | undefined): Promise<Record<string, Partial<Candidate> & { poseUrl?: string }>> {
  if (!runId) return {};
  const runPayload = await fetchRunPayload(runId);
  const candidateIds = new Set(
    (Array.isArray(runPayload.candidates) ? runPayload.candidates : [])
      .map((candidate) => candidate && typeof candidate === 'object'
        ? stringValue((candidate as Record<string, unknown>).id || (candidate as Record<string, unknown>).candidate_id)
        : '')
      .filter(Boolean),
  );
  if (candidateIds.size === 0) return {};

  const jobsResponse = await get<{ jobs?: Array<{ job_id?: string; status?: string }> }>('/selectivity/jobs');
  const completedJobs = (jobsResponse.jobs ?? []).filter((job) => job.status === 'completed' && job.job_id);
  const selectivityByCandidate: Record<string, Partial<Candidate> & { poseUrl?: string }> = {};

  for (const job of completedJobs.slice().reverse()) {
    const results = await get<{ candidates?: unknown[] }>(`/selectivity/results/${job.job_id}`);
    for (const candidate of results.candidates ?? []) {
      const adapted = adaptSelectivityEntry(candidate);
      if (!adapted.id || !candidateIds.has(adapted.id) || selectivityByCandidate[adapted.id]) continue;
      selectivityByCandidate[adapted.id] = adapted;
    }
    if (Object.keys(selectivityByCandidate).length >= candidateIds.size) break;
  }

  return selectivityByCandidate;
}

// ─────────────────────────────────────────────────────────────────────────────
// Run status — polled

export function useRuns() {
  return useQuery<RunsResponse>({
    queryKey: ['runs'],
    queryFn: () => get<RunsResponse>('/runs'),
    staleTime: 30_000,
  });
}

export function useRunStatus(runId: string | undefined) {
  return useQuery<RunStatus>({
    queryKey: ['status', runId],
    queryFn: async () => adaptRunStatus(await fetchRunPayload(runId)),
    refetchInterval: 5000,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Candidates

export function useCandidates(runId: string | undefined) {
  return useQuery<{ run_id: string; wild_type: string; candidates: Candidate[] }>({
    queryKey: ['candidates', runId],
    queryFn: async () => adaptCandidatesPayload(await fetchRunPayload(runId)),
    enabled: !!runId,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Pipeline (per silo)

export function usePipeline(silo: Silo, runId?: string) {
  const siloKey = silo === 'A+B' ? 'Combined' : silo;
  const qs = runId ? `?run_id=${runId}` : '';
  return useQuery<PipelineResponse>({
    queryKey: ['pipeline', siloKey, runId],
    queryFn: () => get<PipelineResponse>(`/pipelines/${siloKey}${qs}`),
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Selectivity matrix

export function useSelectivity(runId: string | undefined) {
  return useQuery<Record<string, Partial<Candidate> & { poseUrl?: string }>>({
    queryKey: ['selectivity', runId],
    queryFn: () => fetchSelectivityPayload(runId),
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
        method: 'PUT',
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
  return useQuery<BenchmarkResponse>({
    queryKey: ['benchmark', phase],
    queryFn: () => get<BenchmarkResponse>(`/benchmark/results?phase=${phase}`),
    staleTime: 5 * 60_000,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Wetlab

export function useWetlabOrders() {
  return useQuery<WetlabOrderListResponse>({
    queryKey: ['wetlab_orders'],
    queryFn: () => get<WetlabOrderListResponse>('/wetlab/orders'),
  });
}

export function useWetlabOrder(orderId: string | undefined) {
  return useQuery<WetlabOrder>({
    queryKey: ['wetlab_order', orderId],
    queryFn: () => get<WetlabOrder>(`/wetlab/orders/${orderId}`),
    enabled: !!orderId,
  });
}

export function useCreateWetlabOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateWetlabOrderRequest) =>
      post<WetlabOrder>('/wetlab/orders', payload),
    onSuccess: (order) => {
      qc.invalidateQueries({ queryKey: ['wetlab_orders'] });
      qc.invalidateQueries({ queryKey: ['wetlab_order', order.id] });
    },
  });
}

export function useTransitionWetlabOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, to_stage, note }: { orderId: string; to_stage: WetlabStage; note?: string }) =>
      post<WetlabOrder>(`/wetlab/orders/${orderId}/transition`, { to_stage, note }),
    onSuccess: (_data, { orderId }) => {
      qc.invalidateQueries({ queryKey: ['wetlab_order', orderId] });
      qc.invalidateQueries({ queryKey: ['wetlab_orders'] });
    },
  });
}
