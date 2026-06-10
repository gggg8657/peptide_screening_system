#!/bin/bash
# Qwen3-32B를 H100(물리 GPU 2번)에 vLLM OpenAI 호환 서버로 기동
export CUDA_VISIBLE_DEVICES=2
exec ~/miniforge3/envs/vllm-server/bin/python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-32B \
  --revision 9216db5781bf21249d130ec9da846c4624c16137 \
  --served-model-name qwen3-32b \
  --port 8000 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 16384 \
  --no-enable-log-requests
# 2026-06-09 (D4/재현성): --revision 으로 모델 버전 고정. HF 캐시 스냅샷과 일치 →
# 업스트림이 가중치를 갱신해도 동일 모델로 재현. 변경 시 캐시 revision 확인 후 갱신.
