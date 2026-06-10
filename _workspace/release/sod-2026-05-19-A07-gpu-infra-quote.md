# A-07 GPU 인프라 견적 자동화 — 시스템 점검 + 견적 템플릿
- 작성일: 2026-05-19
- 담당 에이전트: engineer-infra
- 근거 파일: `docs/meet_log/2026-04-06_action_items/A-07_GPU_infra_quote.md`

---

## 1. 현재 로컬 H100 NVL × 4 점검 결과 (2026-05-19 스냅샷)

### 1.1 GPU별 VRAM 현황

| GPU | 모델 | 전체 VRAM | 사용 중 | 여유 | 온도 | 전력 | 상태 |
|-----|------|-----------|---------|------|------|------|------|
| GPU 0 | NVIDIA H100 NVL | 93.6 GB | **87.6 GB** | 5.4 GB | 46°C | 94.4 W | 점유 (프로세스 PID 4118685) |
| GPU 1 | NVIDIA H100 NVL | 93.6 GB | **87.3 GB** | 5.8 GB | 48°C | 93.4 W | 점유 (프로세스 PID 4118686) |
| GPU 2 | NVIDIA H100 NVL | 93.6 GB | 14 MiB | **93.1 GB** | 37°C | 60.6 W | **유휴 (사용 가능)** |
| GPU 3 | NVIDIA H100 NVL | 93.6 GB | 14 MiB | **93.1 GB** | 38°C | 60.9 W | **유휴 (사용 가능)** |

> 원시 nvidia-smi 출력 (MiB 단위):
> ```
> 0, NVIDIA H100 NVL, 95830, 5546, 89785, 0%, 0%, 46°C, 94.41W/400W
> 1, NVIDIA H100 NVL, 95830, 5914, 89417, 0%, 0%, 48°C, 93.40W/400W
> 2, NVIDIA H100 NVL, 95830, 95317,    14, 0%, 0%, 37°C, 60.60W/400W
> 3, NVIDIA H100 NVL, 95830, 95317,    14, 0%, 0%, 38°C, 60.86W/400W
> ```

### 1.2 점유 프로세스 분석

GPU 0 및 GPU 1에서 각각 ~87–88 GB VRAM을 점유하는 프로세스(PID 4118685, 4118686)가 확인되었다.
`ps` 조회 시 해당 PID가 현재 시스템 프로세스 목록에 없어 **좀비 프로세스 또는 다른 네임스페이스/컨테이너 내부 프로세스**로 추정된다.

- GPU 0, 1: 각 약 87–88 GB 점유 — 대형 LLM 또는 확산 모델 실행 중 가능성 높음
- GPU 2, 3: 14 MiB (드라이버 예약분만 사용) — 즉시 사용 가능

**현재 CUDA_VISIBLE_DEVICES=2** (`~/.zshrc` 설정) → 파이프라인은 GPU 2만 사용 중. GPU 3 추가 병렬화 가능.

### 1.3 NVLink / 인터커넥트 토폴로지

```
        GPU0    GPU1    GPU2    GPU3
GPU0     X      SYS     SYS     SYS
GPU1    SYS      X      SYS     SYS
GPU2    SYS     SYS      X      SYS
GPU3    SYS     SYS     SYS      X
```

**판정: NVLink 미연결 (SYS = PCIe + NUMA 크로스 연결)**

- 4개 GPU 모두 PCIe Gen 5 × 16 연결 (각기 다른 NUMA 노드)
- NVLink 직결 없음 → GPU 간 직접 피어 통신 없이 CPU 메모리 경유
- **단일 fabric 메모리 통합 불가**: GPU 메모리 합산(384 GB)을 단일 주소 공간으로 쓸 수 없음
- 멀티-GPU 분산 추론은 PyTorch DDP / FSDP 또는 `accelerate` 라이브러리 필요

### 1.4 호스트 시스템 사양

| 항목 | 사양 |
|------|------|
| CPU | Intel Xeon Platinum 8558 × 2소켓 (192 vCPU 총) |
| RAM | 512 GB (가용: 476 GB) |
| NUMA 노드 | 4개 (GPU당 1 NUMA 노드) |
| 스토리지 | 848 GB 루트 (사용: 90 GB / 716 GB 여유) |
| 드라이버 VBIOS | 96.00.74.00.11 |
| PCIe | Gen 5 × 16 (전 GPU) |

---

## 2. 현재 워크로드별 GPU 점유 분석

### 2.1 파이프라인 컴포넌트별 VRAM 추정 (H100 NVL 96 GB 기준)

| 컴포넌트 | 추정 VRAM | 현재 GPU | 비고 |
|---------|-----------|----------|------|
| ESMFold | ~16–20 GB | GPU 2 | bio-tools 환경 |
| ProteinMPNN | ~1–2 GB | GPU 2 | bio-tools 환경 |
| RFdiffusion | ~8–12 GB | GPU 2 | rfdiffusion 환경 |
| DiffPepDock | ~10–16 GB | GPU 2 | diffpepdock 환경 |
| Boltz-1 | ~20–30 GB | GPU 2 | PyTorch 2.x |
| PyRosetta | CPU 위주 | N/A | GPU 미사용 |
| **합산 단일 실행** | **~50–75 GB** | GPU 2 | GPU 2의 93 GB로 커버 가능 |
| **병렬 실행 (두 모델 동시)** | **~100–130 GB** | GPU 2+3 필요 | GPU 2 단독 시 OOM 위험 |

### 2.2 병목 식별

1. **단기 병목**: GPU 0, 1이 ~87 GB 점유 상태 — 다른 팀/작업이 전체 용량 사용 중
2. **CUDA_VISIBLE_DEVICES=2 고정**: GPU 2만 노출되어 대형 모델 병렬 실행 불가
3. **NVLink 미연결**: 4 GPU 간 메모리 직접 공유 불가 → 단일 모델의 120 GB+ VRAM 요구는 충족 불가

> **결론**: 현재 H100 NVL × 4 환경에서 단일 GPU 기준 최대 96 GB 확보 가능하며, DiffDock-PP 등 120 GB+ 요구 모델은 단일 GPU로 불가. NVLink 없으므로 단순 multi-GPU tensor parallelism 수동 구현 필요.

---

## 3. 외부망 서버 (H100 × 8) 점검 현황

**상태: 사용자 직접 점검 필요** (외부망 접근 불가)

```bash
# 외부망 서버 접속 후 실행 명령
nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used \
  --format=csv,noheader,nounits
nvidia-smi topo -m
nvidia-smi pmon -c 1
```

| 확인 항목 | 예상값 | 실측값 |
|----------|--------|--------|
| GPU 모델 | H100 SXM 80GB × 8 | — (미확인) |
| 총 VRAM | 640 GB | — (미확인) |
| NVLink 토폴로지 | NV12 (H100 SXM 기준) | — (미확인) |
| 현재 사용 중 VRAM | — | — (미확인) |
| 단일 fabric 통합 가능 여부 | NVLink 존재 시 가능 | — (미확인) |

> **담당**: AI팀 (서호성 / 안기범)이 외부망 접속 후 위 명령 실행 → 결과를 본 문서에 기입 요망

---

## 4. 디퓨전 모델 PoC VRAM 실측 (A-06 연동)

**상태: A-06 완료 후 기입 예정**

| 측정 항목 | 값 |
|----------|-----|
| 모델 로딩 peak VRAM | A-06 완료 후 기입 |
| 배치 추론 peak VRAM | A-06 완료 후 기입 |
| 단일 GPU(96 GB) 충분 여부 | A-06 완료 후 판단 |
| multi-GPU 필요 여부 | A-06 완료 후 판단 |

VRAM 측정 스크립트 (A-06 실행 시 사용):

```bash
# 터미널 1: 모델 실행
CUDA_VISIBLE_DEVICES=2 python run_diffusion_poc.py

# 터미널 2: 실시간 VRAM 모니터링 (1초 간격)
watch -n 1 "nvidia-smi --query-gpu=index,memory.used,memory.free \
  --format=csv,noheader,nounits -i 2"

# 피크 기록용 (백그라운드 로깅)
while true; do
  nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits -i 2 \
    >> /tmp/vram_peak_log.csv
  sleep 0.5
done &
```

---

## 5. 신규 GPU 서버 견적 비교 매트릭스

> **주의**: 아래 가격은 공개 자료 기반 참고치이며, 실제 견적은 벤더로부터 직접 수집해야 합니다.

### 5.1 옵션 비교 (현재 워크로드 기준: PyRosetta + Boltz + ESM + ProteinMPNN)

| 항목 | 현재 로컬 H100 NVL × 4 | 외부망 H100 SXM × 8 | NVIDIA DGX H100 | NVIDIA DGX B200 | 자체 빌드 H100 SXM × 8 |
|------|:---:|:---:|:---:|:---:|:---:|
| **GPU 모델** | H100 NVL | H100 SXM | H100 SXM | B200 | H100 SXM |
| **단일 GPU VRAM** | 96 GB | 80 GB | 80 GB | 180 GB | 80 GB |
| **GPU 수** | 4 | 8 | 8 | 8 | 8 |
| **총 VRAM** | 384 GB | 640 GB | 640 GB | 1,440 GB | 640 GB |
| **NVLink** | **없음 (PCIe only)** | 확인 필요 | NVLink 4 (900 GB/s) | NVLink 5 (1,800 GB/s) | 구성 의존 |
| **단일 fabric 통합** | **불가** | 확인 필요 | 가능 (NVSwitch) | 가능 (NVSwitch) | NVLink 탑재 시 가능 |
| **FP8 연산 성능** | ~3.9 PFLOPS × 4 | ~3.9 PFLOPS × 8 | ~3.9 PFLOPS × 8 | ~9.0 PFLOPS × 8 | ~3.9 PFLOPS × 8 |
| **전력 요구사항** | ~1,600 W | — | ~10,200 W | ~14,300 W | 구성 의존 |
| **냉각 방식** | 공냉 | — | 액냉/공냉 선택 | 액냉 권장 | 구성 의존 |
| **랙 유닛** | — | — | 10U | 10U | 구성 의존 |
| **120 GB+ 단일 모델 요건 충족** | 불가 (96 GB 최대) | NVLink 시 가능 | NVLink 통합 시 가능 | **가능 (180 GB 단일 GPU)** | NVLink 시 가능 |
| **추정 가격 (USD, 참고치)** | 보유 중 | 보유 중 | **$350,000–$400,000** | **$500,000–$600,000** | **$150,000–$200,000** |
| **추정 가격 (KRW, 참고치)** | — | — | 약 4.8–5.5억 원 | 약 6.8–8.2억 원 | 약 2.0–2.7억 원 |
| **납기 (참고치)** | N/A | N/A | 12–24주 | 24–36주 (공급 제한) | 8–16주 |
| **유지보수 계약** | — | — | NVIDIA AI Enterprise | NVIDIA AI Enterprise | 벤더 의존 |
| **벤더 견적 A (실수치)** | N/A | N/A | **TBD** | **TBD** | **TBD** |
| **벤더 견적 B (실수치)** | N/A | N/A | **TBD** | **TBD** | **TBD** |

> 가격 출처: NVIDIA 공식 MSRP 참고치 (2025년 기준), KRW는 1 USD = 1,370 KRW 기준.
> 국내 공공기관 조달 시 G2B(나라장터) 또는 NVIDIA 공인 리셀러(삼성SDS, LG CNS, SK C&C 등) 견적 필수.

### 5.2 벤더 견적 수집 체크리스트 (서호성 / 안기범 담당)

- [ ] **옵션 A — NVIDIA DGX H100**
  - NVIDIA 직접 또는 공인 리셀러 (삼성SDS, LG CNS, SK C&C)
  - 견적 요청 시 포함 사항: 시스템 가격 + 유지보수 3년 + 설치 지원
- [ ] **옵션 B — NVIDIA DGX B200**
  - 납기 및 공급 가능 여부 우선 확인 (2025–2026 공급 제한 예상)
- [ ] **옵션 C — 자체 빌드 H100 SXM × 8 (OEM)**
  - 추천 OEM: Dell PowerEdge XE9680, HPE ProLiant DL980 Gen10, Supermicro SYS-821GE-TNHR
  - NVLink 지원 여부 및 NVSwitch 포함 여부 명시 요청
- [ ] 국내 조달 가능 여부 및 G2B 등록 여부 확인
- [ ] 전력/냉각 인프라 요구사항 확인 (데이터센터 수용 가능 여부)

---

## 6. 추천 및 의사결정 가이드

### 6.1 현재 워크로드 적합성 평가

```
현재 워크로드: PyRosetta (CPU) + Boltz (~25 GB) + ESMFold (~18 GB) + ProteinMPNN (~2 GB)
                + RFdiffusion (~10 GB) + DiffPepDock (~14 GB)

단일 순차 실행: ~50–70 GB → 현재 GPU 2 (96 GB) 으로 커버 가능
병렬 실행 (2 모델 동시): ~100–130 GB → GPU 2+3 필요 (NVLink 없으므로 수동 분배)
120 GB+ 단일 모델 (DiffDock-PP 등): 현재 환경에서 불가
```

### 6.2 단계별 의사결정 트리

```
[1단계] 외부망 H100 × 8 NVLink 통합 가능?
    YES → 기존 640 GB 인프라 활용, 추가 구매 보류
    NO  → [2단계]로

[2단계] A-06 PoC peak VRAM ≤ 96 GB?
    YES → 현재 H100 NVL GPU 2/3 활용으로 충분
          CUDA_VISIBLE_DEVICES=2,3 설정 변경으로 대응 가능
    NO  → [3단계]로

[3단계] A-06 PoC peak VRAM ≤ 640 GB?
    YES (120–640 GB) → 외부망 H100 × 8 NVLink 확보가 최우선 (추가 구매 전)
    NO (> 640 GB) → DGX B200 (180 GB 단일 GPU) 검토 필요
```

### 6.3 옵션별 추천 우선순위 (2026-05-19 현재)

| 순위 | 옵션 | 사유 |
|------|------|------|
| 1순위 | **외부망 H100 × 8 NVLink 통합** | 보유 자산 활용, 추가 비용 없음 — 선결 확인 필요 |
| 2순위 | **현재 로컬 GPU 2+3 병렬 사용** | CUDA_VISIBLE_DEVICES=2,3 설정만으로 즉시 적용 가능 |
| 3순위 | **자체 빌드 H100 SXM × 8** | DGX 대비 50–60% 비용, 구성 유연성, NVLink 선택 가능 |
| 4순위 | **DGX H100** | 검증된 솔루션, 즉시 운영 가능하나 높은 비용 |
| 5순위 | **DGX B200** | 단일 GPU 180 GB로 120 GB+ 요건 단독 충족, 최고 가격 + 납기 리스크 |

---

## 7. 즉시 적용 가능한 인프라 개선 (추가 구매 불필요)

### 7.1 GPU 2+3 병렬화 (당장 실행 가능)

```bash
# ~/.zshrc 수정 — GPU 2, 3 동시 사용
export CUDA_VISIBLE_DEVICES=2,3

# 검증
python -c "import torch; print(torch.cuda.device_count(), torch.cuda.get_device_name(0))"
```

예상 효과: 최대 192 GB VRAM 가용 (배치 처리 2배 향상)

### 7.2 GPU 0, 1 점유 프로세스 정리 (관리자 협조 필요)

현재 GPU 0, 1에 각 ~87 GB 점유 프로세스가 컨테이너/다른 네임스페이스에서 실행 중.
해당 작업 종료 시 추가 192 GB 확보 가능.

```bash
# 점유 프로세스 UUID 확인
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
# → PID 4118685, 4118686 (현재 ps에서 조회 불가 — 컨테이너 내부 추정)
```

### 7.3 VRAM 모니터링 자동화 스크립트

```bash
# /home/dongjukim/scripts/gpu_monitor.sh
#!/bin/bash
LOG=/tmp/gpu_vram_$(date +%Y%m%d_%H%M%S).csv
echo "timestamp,gpu,used_mib,free_mib,temp_c,power_w" > $LOG
while true; do
  ts=$(date +%H:%M:%S)
  nvidia-smi --query-gpu=index,memory.used,memory.free,temperature.gpu,power.draw \
    --format=csv,noheader,nounits | awk -v ts="$ts" '{print ts","$0}' >> $LOG
  sleep 5
done
```

---

## 8. 검증 기준 (Acceptance Criteria) 현황

| 기준 | 상태 |
|------|------|
| 사용자 로컬 H100 NVL × 4 점검 결과 기록 | **완료** (섹션 1) |
| 외부망 H100 × 8 NVLink topology 확인 | **미완료** — 사용자 직접 확인 필요 |
| A-06 PoC peak VRAM 수치 기록 | **미완료** — A-06 완료 후 기입 |
| 최소 2개 벤더 견적 입력란 작성 | **부분 완료** — 가이드 템플릿 준비, 실수치는 사용자 수집 필요 |
| "기존 H100 × 8 활용 가능 여부" 결론 | **보류** — NVLink topology 확인 후 판단 가능 |
| 추가 구매 필요 여부 의사결정 결론 | **보류** — 외부망 점검 + A-06 PoC 후 판단 가능 |

---

## 9. 다음 액션 (담당자별)

| 담당 | 액션 | 우선순위 |
|------|------|---------|
| AI팀 (engineer-infra) | `CUDA_VISIBLE_DEVICES=2,3` 병렬 테스트 실행 | 즉시 |
| AI팀 | 외부망 서버 `nvidia-smi topo -m` 실행 + 결과 기입 | 이번 주 |
| AI팀 | A-06 PoC 실행 시 VRAM 피크 기록 | A-06 일정에 따름 |
| 서호성 / 안기범 | 벤더 최소 2곳 공식 견적 수집 (섹션 5.2 체크리스트) | 5월 회의 전 |
| 서호성 / 안기범 | 수집 견적을 `A-07_GPU_infra_quote.md` TBD 칸에 기입 | 견적 수집 즉시 |

---

*작성: engineer-infra (claude-sonnet-4-6) — 2026-05-19*
*참고: `docs/meet_log/2026-04-06_action_items/A-07_GPU_infra_quote.md`, NVIDIA 공식 자료*
