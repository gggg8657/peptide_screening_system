# figures — 미팅용 Mermaid 다이어그램

소스는 `.mmd` 파일입니다. 슬라이드에 넣으려면 PNG/SVG로 내보낸 뒤 Marp에 이미지로 삽입하세요.

---

## 파일

| 파일 | 내용 |
|------|------|
| `fig01_pipeline_flow.mmd` | Silo A/B 파이프라인 흐름 |
| `fig02_cluster_classification.mmd` | A~E 클러스터 |
| `fig03_pepadmet_models.mmd` | pepADMET 모델 그룹 |

---

## PNG 일괄 변환 (예시)

이 디렉터리에서:

```bash
for f in *.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.png" -w 2400 -H 1600
done
```

`mmdc`는 `@mermaid-js/mermaid-cli` 패키지입니다 (`npm i -g @mermaid-js/mermaid-cli`).

레포 루트에서 실행할 때는 경로만 맞추면 됩니다:

```bash
for f in docs/presentation_20260330/figures/*.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.png" -w 2400 -H 1600
done
```
