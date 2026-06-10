# SOD 2026-05-20 — vLLM 다중 인스턴스 가동 보고서

**작성**: engineer-infra  
**날짜**: 2026-05-20 07:33 UTC  
**Task**: #12 vLLM 추가 모델 가동 (GPU 2/3 idle 활용)

---

## §1 환경 인벤토리 — GPU 점유 현황

### 작업 전 GPU 상태

| GPU | 모델 | Used (MiB) | Free (MiB) | Total (MiB) | 비고 |
|-----|------|-----------|-----------|-------------|------|
| 0 | H100 NVL | 89,787 | 5,544 | 95,830 | PID 4118685 좀비 (Not Found) |
| 1 | H100 NVL | 89,417 | 5,914 | 95,830 | PID 4118686 좀비 (Not Found) |
| 2 | H100 NVL | 2,481 | 92,850 | 95,830 | PID 702421 (미확인 프로세스) |
| 3 | H100 NVL | 14 | 95,317 | 95,830 | 완전 유휴 |

### 작업 후 GPU 상태

| GPU | Used (MiB) | Free (MiB) | 점유 프로세스 |
|-----|-----------|-----------|-------------|
| 0 | 89,787 | 5,544 | PID 4118685 (좀비, 변동 없음) |
| 1 | 89,417 | 5,914 | PID 4118686 (좀비, 변동 없음) |
| 2 | 14 | 95,317 | 없음 (PID 702421 자연 해제됨) |
| 3 | **86,287** | **9,044** | **PID 717538 — DeepSeek-R1-Distill-32B** |

> **참고**: GPU 2의 PID 702421 (2,481 MiB 점유)은 새 인스턴스 가동 과정에서 자연 해제됨.  
> 포트 8000의 qwen3.5-35b-a3b는 가동 중이며 GPU 점유 표시가 없는 상태임 (다른 namespace 가능성).

### 디스크 현황

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme1n1p1  7.0T  6.4T  210G  97% /home/dongjukim
```

> **주의**: 97% 사용. 신규 모델 다운로드 불필요 (기존 캐시 활용).

---

## §2 새 vLLM 인스턴스 정보

### 가동 명령

```bash
MODEL_PATH="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"

CUDA_VISIBLE_DEVICES=3 conda run --no-capture-output -n vllm-server \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1-distill-32b" \
    --host 127.0.0.1 \
    --port 8001 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.88 \
    --dtype bfloat16 \
  > /tmp/vllm_8001.log 2>&1 &
```

### 인스턴스 상세

| 항목 | 값 |
|------|-----|
| **Model ID** | `deepseek-r1-distill-32b` |
| **HF repo** | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` |
| **Snapshot** | `711ad2ea6aa40cfca18895e8aca02ab92df1a746` |
| **Port** | `8001` |
| **Host** | `127.0.0.1` |
| **GPU** | GPU 3 (`CUDA_VISIBLE_DEVICES=3`) |
| **GPU UUID** | `GPU-e11ec417-e009-eb10-4134-ade9e5826062` |
| **VRAM 사용** | 86,264 MiB (~84.3 GB) |
| **모델 가중치** | 61.06 GiB (bfloat16) |
| **max_model_len** | 32,768 tokens |
| **KV cache** | 75,216 tokens |
| **최대 동시성** | 2.30× (@ 32768 tokens/req) |
| **vLLM 버전** | 0.18.1 |
| **conda env** | `vllm-server` |
| **부팅 소요시간** | ~90초 (가중치 로드 30초 + 컴파일 21초 + CUDA graph 10초 + warmup) |

### 로그 위치

```
/tmp/vllm_8001.log
```

### 부팅 확인

```
INFO 05-20 07:33:31 [api_server.py:580] Starting vLLM server on http://127.0.0.1:8001
INFO:     Application startup complete.
```

---

## §3 호출 검증 결과

### 검증 1 — 기본 응답 (pong 테스트)

```bash
curl -s -m 60 -X POST http://localhost:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer EMPTY' \
  -d '{"model":"deepseek-r1-distill-32b","messages":[{"role":"user","content":"Reply with exactly: pong"}],"max_tokens":50,"temperature":0}'
```

| 항목 | 결과 |
|------|------|
| **HTTP 응답** | 200 OK |
| **Latency** | 1,133 ms |
| **JSON 파싱** | 성공 |
| **finish_reason** | `length` (max_tokens=50 도달) |
| **모델 응답** | 추론 과정 포함 (DeepSeek CoT 특성) |

> **참고**: DeepSeek-R1 계열은 CoT reasoning이 기본 활성화. `<think>...</think>` 형태의 추론 과정이 응답 앞에 포함됨.

### 검증 2 — /v1/models 엔드포인트

```bash
curl -s http://localhost:8001/v1/models
```

```json
{
  "id": "deepseek-r1-distill-32b",
  "root": "/home/.../DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea...",
  "max_model_len": 32768
}
```

**결과**: 정상 ✅

---

## §4 다중 모델 비교 실측

**동일 프롬프트**: `"What is the SSTR2 receptor and why is it important for cancer drug development? Answer in 2 sentences."`

### Port 8000 — qwen3.5-35b-a3b (Qwen/Qwen3.5-35B-A3B, MoE)

| 항목 | 값 |
|------|-----|
| **Latency** | **503 ms** |
| **응답 스타일** | 직접적 2문장 답변 |
| **CoT** | 비활성 (`enable_thinking: false`) |
| **응답 품질** | 전문적, 정확, 간결 |

**응답 (요약)**:
> "The SSTR2 (Somatostatin Receptor 2) is a G-protein coupled receptor frequently overexpressed on the surface of various neuroendocrine tumors and other cancers, where it regulates cell growth and secretion. Its importance in drug development stems from its role as a highly specific target for radioligand therapy..."

### Port 8001 — deepseek-r1-distill-32b (Dense 32B)

| 항목 | 값 |
|------|-----|
| **Latency** | **6,586 ms** |
| **응답 스타일** | 추론 과정 + 최종 답변 |
| **CoT** | 항상 활성 (R1 특성) |
| **응답 품질** | 단계적 추론, 자가 검증 포함 |

**응답 특성**: 먼저 "SSTR stands for Somatostatin Receptor. Somatostatin is a hormone..." 식으로 추론을 전개한 뒤 결론 도출. 심화 분석이 필요한 경우 유리.

### 비교 요약

| 비교 항목 | qwen3.5-35b-a3b (8000) | deepseek-r1-distill-32b (8001) |
|-----------|------------------------|-------------------------------|
| **Latency** | ~500ms (빠름) | ~6,500ms (느림, CoT 비용) |
| **응답 스타일** | 직접 답변 | 추론 + 답변 |
| **적합 task** | 빠른 생성, 요약, 보고 | 복잡한 계획, 단계 추론, 검증 |
| **아키텍처** | MoE (35B total / 3.5B active) | Dense 32B |
| **VRAM 추정** | ~3.5 GB 활성 (MoE 효율) | ~84 GB (Dense full load) |

---

## §5 권고 + pipeline_config.yaml.agents 섹션 권장값

### 모델-Agent 매핑 권고

각 에이전트의 특성에 따라 최적 모델을 배정:

```yaml
# 권장 pipeline_config.yaml (코드 변경 없음, 설정만 참고)
llm:
  agents:
    # CoT 추론이 필요한 에이전트 → deepseek-r1-distill-32b
    planner:
      provider: "vllm"
      model: "deepseek-r1-distill-32b"
      base_url: "http://localhost:8001"
      # 장점: 단계별 mutation 계획, 복잡한 시퀀스 설계에 추론 필요
      # 주의: latency ~6-10s, max_tokens 충분히 (≥500) 설정

    # 빠른 생성/요약이 필요한 에이전트 → qwen3.5-35b-a3b
    critic:
      provider: "vllm"
      model: "qwen3.5-35b-a3b"
      base_url: "http://localhost:8000"
      # 장점: 빠른 응답, 직관적 평가
    
    reporter:
      provider: "vllm"
      model: "qwen3.5-35b-a3b"
      base_url: "http://localhost:8000"
      # 장점: 요약/보고 형태 출력에 최적

    # 비교 실험 시 A/B 배정 예시
    # planner_a: 8000 (qwen3.5), planner_b: 8001 (deepseek-r1)
```

### 주의사항

1. **DeepSeek-R1 CoT 처리**: 응답에 `<think>...</think>` 블록 포함 가능 → 파이프라인에서 별도 파싱 필요
2. **Latency SLA**: planner에 deepseek-r1 배정 시 step timeout을 최소 30초로 늘려야 함 (현재 기본값 확인 필요)
3. **재시작 방법**: `/tmp/vllm_8001.log` 확인 후 PID kill → 동일 명령 재실행
4. **GPU 3 전용**: 다른 작업에서 `CUDA_VISIBLE_DEVICES=3` 사용 금지

---

## 부록 — 재가동 스크립트

```bash
#!/bin/bash
# vLLM port 8001 (DeepSeek-R1-Distill-32B) 재가동
MODEL_PATH="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"

CUDA_VISIBLE_DEVICES=3 conda run --no-capture-output -n vllm-server \
  python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "deepseek-r1-distill-32b" \
    --host 127.0.0.1 \
    --port 8001 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.88 \
    --dtype bfloat16 \
  > /tmp/vllm_8001.log 2>&1 &

echo "PID=$!"
echo "Waiting for startup..."
until grep -q "Application startup complete" /tmp/vllm_8001.log 2>/dev/null; do sleep 5; done
echo "Ready! curl http://localhost:8001/v1/models"
```
