/**
 * useBindingPocket — SSTR1~5 바인딩 포켓 좌표·반경·잔기 CRUD 훅
 *
 * 위치: src/hooks/useBindingPocket.ts
 *
 * BE API (be-binding-api, task #1 완료 / uvicorn 재기동 후 활성):
 *   GET    /api/binding_pocket/{receptor}          → BindingPocketConfig
 *   PUT    /api/binding_pocket/{receptor}          → PutResponse {ok, path}
 *   POST   /api/binding_pocket/{receptor}/extract  → BindingPocketConfig (source="auto_extract")
 *   DELETE /api/binding_pocket/{receptor}          → DeleteResponse {ok, restored}
 *
 * 주의:
 *   - BE 수용체명은 소문자 (sstr1~sstr5). UI 탭은 대문자(SSTR1~5) 그대로 유지.
 *     toApiReceptor() 가 변환 담당.
 *   - SSTR1/3/4/5는 현재 서버에 설정 파일 없음 → GET 404 → isError=true
 *     컴포넌트는 DEFAULT_CONFIGS 폴백으로 작동.
 *   - uvicorn 재기동 전까지는 404/Connection Refused → mock dev 모드로 진행.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// ─────────────────────────────────────────────────────────────────────────────
// Types

export type BindingPocketConfig = {
  receptor: string             // 내부적으로 소문자("sstr2"), 표시는 대문자로 변환
  center_x: number
  center_y: number
  center_z: number
  radius_angstrom: number      // 5.0~30.0 Å
  residue_ids: number[]
  /** null → 서버 측 자동 계산 (radius×2, 최소 30Å) */
  box_size?: { size_x: number; size_y: number; size_z: number } | null
  /** "user_override" | "auto_extract" | "PDB_3SST" | "literature" */
  source: string
  timestamp?: string
}

/** PUT 성공 응답 */
export type PutResponse = { ok: boolean; path: string }

/** DELETE 성공 응답 */
export type DeleteResponse = { ok: boolean; restored: boolean }

/** extract mutation 입력 */
export type ExtractInput = {
  receptor: string
  residue_ids: number[]   // 1개 이상 필수 — 서버가 해당 잔기 기반으로 포켓 중심 계산
}

// ─────────────────────────────────────────────────────────────────────────────
// 수용체명 변환

/** UI 대문자 → API 소문자 ("SSTR2" → "sstr2") */
export function toApiReceptor(receptor: string): string {
  return receptor.toLowerCase()
}

// ─────────────────────────────────────────────────────────────────────────────
// Fetch helpers

const BASE = '/api'

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

async function apiPostWithBody<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks

/**
 * 특정 수용체의 바인딩 포켓 설정 조회.
 * 404 (SSTR1/3/4/5 등 미설정) → isError=true → 컴포넌트가 DEFAULT_CONFIGS 폴백.
 */
export function useBindingPocket(receptor: string) {
  return useQuery<BindingPocketConfig>({
    queryKey: ['binding_pocket', receptor],
    queryFn: () =>
      apiGet<BindingPocketConfig>(`/binding_pocket/${toApiReceptor(receptor)}`),
    retry: 1,
    staleTime: 60_000,
  })
}

/**
 * 바인딩 포켓 설정 저장 (PUT).
 * - receptor를 소문자로 변환하여 전송.
 * - 성공 시 {ok:true, path} 반환 (BindingPocketConfig 아님).
 * - onSuccess → GET 캐시 무효화 → 자동 재조회.
 */
export function useUpdateBindingPocket() {
  const qc = useQueryClient()
  return useMutation<PutResponse, Error, BindingPocketConfig>({
    mutationFn: (config: BindingPocketConfig) =>
      apiPut<PutResponse>(`/binding_pocket/${toApiReceptor(config.receptor)}`, {
        ...config,
        receptor: toApiReceptor(config.receptor), // BE expects lowercase
      }),
    onSuccess: (_, variables) =>
      qc.invalidateQueries({ queryKey: ['binding_pocket', variables.receptor] }),
  })
}

/**
 * PDB 파일에서 포켓 좌표·잔기 자동 추출 (POST).
 * residue_ids: 1개 이상 필수. 서버가 해당 잔기 좌표 기반으로 포켓 중심 계산.
 * 성공 시 캐시 직접 업데이트 → GET 재요청 생략.
 */
export function useExtractBindingPocket() {
  const qc = useQueryClient()
  return useMutation<BindingPocketConfig, Error, ExtractInput>({
    mutationFn: ({ receptor, residue_ids }: ExtractInput) =>
      apiPostWithBody<BindingPocketConfig>(
        `/binding_pocket/${toApiReceptor(receptor)}/extract`,
        { residue_ids },
      ),
    onSuccess: (data, { receptor }) =>
      qc.setQueryData(['binding_pocket', receptor], data),
  })
}

/**
 * 사용자 오버라이드 초기화 (DELETE).
 * - restored=true: _default.json 백업 복원
 * - restored=false: 오버라이드 파일만 삭제 → 이후 GET → 404
 * onSuccess → GET 캐시 무효화 → 재조회 (404 시 isError=true → DEFAULT_CONFIGS 폴백).
 */
export function useDeleteBindingPocket() {
  const qc = useQueryClient()
  return useMutation<DeleteResponse, Error, string>({
    mutationFn: (receptor: string) =>
      apiDelete<DeleteResponse>(`/binding_pocket/${toApiReceptor(receptor)}`),
    onSuccess: (_, receptor) =>
      qc.invalidateQueries({ queryKey: ['binding_pocket', receptor] }),
  })
}
