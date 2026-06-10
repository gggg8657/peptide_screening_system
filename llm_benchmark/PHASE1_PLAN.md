# Phase 1 실행 계획 v2

## GPU 배치

| Slot | GPU | Port | VRAM |
|------|-----|------|------|
| 0 | GPU 2 | 8003 | 96GB |
| 1 | GPU 3 | 8002 | 96GB |

## 실험 순서

```
Batch 1                                    Batch 2                                    Batch 3
──────────────────────────                 ──────────────────────────                 ──────────────────────────
GPU 2: M1 Qwen2.5-7B                      GPU 2: M3 Qwen3-32B                       
GPU 3: M2 Qwen3.5-27B                     GPU 3: M4 DeepSeek-R1-32B                 GPU 3: M5 GLM-Z1-32B

P1-01  7B   s42   static   :8003          P1-13  32B-Q  s42   static   :8003        P1-25  32B-GL s42   static   :8002
P1-02  7B   s137  static   :8003          P1-14  32B-Q  s137  static   :8003        P1-26  32B-GL s137  static   :8002
P1-03  7B   s256  static   :8003          P1-15  32B-Q  s256  static   :8003        P1-27  32B-GL s256  static   :8002
P1-04  7B   s42   adaptive :8003          P1-16  32B-Q  s42   adaptive :8003        P1-28  32B-GL s42   adaptive :8002
P1-05  7B   s137  adaptive :8003          P1-17  32B-Q  s137  adaptive :8003        P1-29  32B-GL s137  adaptive :8002
P1-06  7B   s256  adaptive :8003          P1-18  32B-Q  s256  adaptive :8003        P1-30  32B-GL s256  adaptive :8002
P1-07  27B  s42   static   :8002          P1-19  32B-DS s42   static   :8002
P1-08  27B  s137  static   :8002          P1-20  32B-DS s137  static   :8002
P1-09  27B  s256  static   :8002          P1-21  32B-DS s256  static   :8002
P1-10  27B  s42   adaptive :8002          P1-22  32B-DS s42   adaptive :8002
P1-11  27B  s137  adaptive :8002          P1-23  32B-DS s137  adaptive :8002
P1-12  27B  s256  adaptive :8002          P1-24  32B-DS s256  adaptive :8002

12 runs 병렬 ~12min                       12 runs 병렬 ~12min                        6 runs 병렬 ~12min
```

## 각 실험 공통 설정

| 항목 | 값 |
|------|-----|
| Flow | Sequential (고정) |
| Candidates/iter | 4 |
| Iterations | 3 |
| Seed | 42, 137, 256 |
| FlexPepDock | CPU 16워커/실험 |
| Template | fold_test1_model_0.pdb |
| LLM temp | 0.3 |
| Gate mode | static / adaptive |

## Adaptive Gate 동작

```
static:   ddG ≤ -5.0, clash ≤ 10 (전 iteration 고정)
adaptive: 초기값 = baseline ddG × 0.1, Critic이 매 iteration 조정
```

## 타임라인

```
00:00  Batch 1 시작 (GPU2=7B, GPU3=27B 로딩 ~2min)
00:15  Batch 1 완료 → Batch 2 모델 교체 (~3min)
00:30  Batch 2 완료 → Batch 3 모델 교체 (~2min)
00:44  Batch 3 완료
00:47  Phase 1 종료 — 30/30 완료
```

**총 소요: ~50분 | 실험 30개 | 모델 교체 3회**

## 실행 명령

```bash
rm -rf llm_benchmark/outputs/phase1/*/
bash llm_benchmark/run_phase1.sh
```

## 완료 후

```bash
python -m llm_benchmark.scoring.aggregate phase1
```
