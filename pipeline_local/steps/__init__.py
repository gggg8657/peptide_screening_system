"""
pipeline_local/steps/__init__.py
=================================
Step 모듈 패키지.

각 step은 독립적으로 임포트 가능하며, 파이프라인 오케스트레이터에서
순서대로 호출된다.

Step 목록:
    step01_receptor         -- SSTR2 수용체 구조 준비 (openfold3)
    step02_backbone         -- de novo 펩타이드 백본 생성 (rfdiffusion)
    step03_sequence         -- 백본당 서열 설계 (proteinmpnn)
    step03b_blosum_mutation -- BLOSUM62 기반 변이 서열 생성
    step04_qc               -- 구조 QC (esmfold, pLDDT 게이트)
    step05_docking          -- 결합 포즈/친화도 평가 (diffpepbuilder, boltz)
    step05b_selectivity     -- 선택성 평가 (off-target 도킹)
    step05c_boltz_cross     -- Boltz-2 selectivity cross-validation (iPTM 매트릭스)
    step06_rosetta          -- FlexPepDock Rosetta 정밀 도킹
    step07_analysis         -- 구조 분석 및 클러스터링
    step08_stability        -- 안정성/반감기 예측
"""

from pipeline_local.steps import (
    step01_receptor,
    step02_backbone,
    step03_sequence,
    step03b_blosum_mutation,
    step04_qc,
    step05_docking,
    step05b_selectivity,
    step05c_boltz_cross,
    step06_rosetta,
    step07_analysis,
    step08_stability,
)
