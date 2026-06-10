# Gemma3 1B + N-Iteration Run Guide

> **최종 업데이트: 2026-03-04**

## 1) Configure defaults
- `AG_src/config/pipeline_config.yaml`
  - `iteration.max_iterations: 10`
  - `llm.model: "qwen3:8b"` (기본값) 또는 `"gemma3:1b"` (경량 폴백)
  - `llm.provider: "ollama"`

## 2) Start from Web UI control panel
1. Start backend API server:
   - `python backend/api_server.py`
2. Start frontend:
   - `cd frontend && npm run dev -- --host`
3. Open dashboard: `http://localhost:5173`
4. In the top control panel, set:
   - `Iterations (N)`
   - `LLM Provider`
   - `LLM Model` (example: `gemma3:1b`)
5. Click `Start Run`.

## 3) Start from CLI directly
- `python run_pipeline_live.py --max-iterations 12 --llm-provider ollama --llm-model gemma3:1b`

Optional:
- `--llm-base-url http://localhost:11434`
- `--run-id live_run_custom_001`

## 4) Backend run control API
- `GET /api/run/status`
- `POST /api/run/start`
- `POST /api/run/stop`

Example start payload:
```json
{
  "max_iterations": 12,
  "llm_provider": "ollama",
  "llm_model": "gemma3:1b"
}
```

## 5) Windows one-command launcher
- `./start_monitoring.ps1 -Iterations 12 -LlmProvider ollama -LlmModel gemma3:1b`

