# Repos — 신뢰도 평가

접근 확인일: 2026-06-01  
평가 기준: GitHub 스타 수, 라이선스, 최근 커밋, 논문 연계, 유지 보수 활성도

| Repo | URL | Stars | License | 최근 릴리스 | 논문 | 유지 활성 | 신뢰도 |
|------|-----|-------|---------|-----------|------|---------|-------|
| gcorso/DiffDock | https://github.com/gcorso/DiffDock | 1.5k | MIT | v1.1.3 (2024-09-04) | ICLR 2023 / arXiv:2210.01776 | 中 (2024 이후 감소) | 高 |
| jwohlwend/boltz | https://github.com/jwohlwend/boltz | 미공개 | MIT | v2.2.1 (2025-09-08) | bioRxiv 2025 / PMC12262699 | 高 (437 커밋, 17 릴리스) | 高 |
| Valdes-Tresanco-MS/gmx_MMPBSA | https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA | 311 | GPL-3.0 | v1.6.5 (2026-05-23) | JCTC 2021 | 高 (2026년 릴리스) | 高 |
| swansonk14/admet_ai | https://github.com/swansonk14/admet_ai | 313 | MIT | v_2.0.1 (2026-02-22) | Bioinformatics 2024 | 高 | 高 |
| ifyoungnet/pepADMET | https://github.com/ifyoungnet/pepADMET | 23 | GPL-3.0 | 미공개 | JCIM 2025/2026 | 低-中 (18 커밋) | 中 |
| anyoptimization/pymoo | https://github.com/anyoptimization/pymoo | 미확인 | Apache-2.0 | v0.6.1.6 | IEEE Access 2020 | 中 | 高 |
| OpenFreeEnergy/openfe | https://github.com/OpenFreeEnergy/openfe | 미확인 | MIT | v1.0+ stable (2024-05) | OMSF 컨소시엄 | 高 | 高 |
| openmm/openmm | https://github.com/openmm/openmm | 미확인 | MIT/LGPL | 8.x | J Phys Chem B 등 | 高 | 高 |
| google-deepmind/alphafold3 | https://github.com/google-deepmind/alphafold3 | 미확인 | custom (비상업) | 2024 | Nature 2024 | 高 | 高 |

## 주요 주의 사항

- **pepADMET**: 커밋 수(18)·스타(23) 낮음 — 논문 신규 발표로 초기 단계. 운영 파이프라인 전 로컬 검증 필요
- **DiffDock**: 소분자 도킹 특화. 펩타이드(SST14 analogue, 14aa) 적용 시 성능 검증 별도 필요
- **AlphaFold3 inference code**: 비상업 라이선스 — KAERI 연구 목적 사용 검토 필요
- **OpenFE 구 도메인(openfree-energy.org)**: ECONNREFUSED — 현행 URL(openfree.energy)로 교체 필수
