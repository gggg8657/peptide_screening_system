"""
Wetlab Order 라우터 — in-vitro Ki binding assay 발주 관리.

데이터 소스 (참조):
  docs/wetlab/cand03_binding_assay_design.md  — 발주 후보 + 비용
  docs/wetlab/halflife_methodology.md          — assay protocol

마운트:
  app.include_router(wetlab.router, prefix="/api/wetlab", tags=["wetlab"])

상태 머신: draft → review → approval → PO → shipped
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..schemas.dashboard import (  # type: ignore
    WetlabOrder, WetlabOrderListItem, WetlabOrderListResponse,
    WetlabTransitionRequest, WetlabStage,
    Reagent, PredictedKi, AcceptanceCriterion, TimelineEntry, WetlabProtocol,
)

router = APIRouter()
KST = timezone(timedelta(hours=9))


def _orders_store() -> Path:
    """JSON 파일 기반 단순 store. 실 운영은 DB 권장."""
    p = Path(__file__).resolve().parents[3] / "runs_local" / "wetlab_orders.json"
    return p


def _load_orders() -> list[dict]:
    p = _orders_store()
    if not p.exists():
        return _seed_orders()
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_orders(orders: list[dict]) -> None:
    p = _orders_store()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2, default=str)


def _seed_orders() -> list[dict]:
    """초기 시드 — cand03 발주 1건."""
    seed = [_build_cand03_order()]
    _save_orders(seed)
    return seed


def _build_cand03_order() -> dict:
    """docs/wetlab/cand03_binding_assay_design.md 기반."""
    return WetlabOrder(
        id="WO-2026-005",
        candidate_id="cand03",
        candidate_seq="AICKNFFWKTFTSC",
        stage="approval",
        total_krw=13_400_000,
        lead_weeks=8,
        requested_by="dongjukim@kaeri.re.kr",
        created_at=datetime(2026, 5, 12, 9, 0, tzinfo=KST),
        hypothesis={
            "h1": "cand03은 SSTR2에 대해 SST-14 대비 향상된 선택성을 보이며 Ki(SSTR2) < 10 nM, log(Ki(SSTR1)/Ki(SSTR2)) > 1.0",
            "h0": "cand03의 5개 SSTR Ki 프로파일이 SST-14와 통계적으로 유의미한 차이가 없다 (ANOVA p > 0.05)",
        },
        predicted_ki=[
            PredictedKi(receptor="SSTR1", iptm=0.900, sst14_ki_nm=0.4, predicted_ki="≥ 5 nM"),
            PredictedKi(receptor="SSTR2", iptm=0.952, sst14_ki_nm=0.2, predicted_ki="0.5–5 nM", target=True),
            PredictedKi(receptor="SSTR3", iptm=0.838, sst14_ki_nm=0.8, predicted_ki="≥ 10 nM"),
            PredictedKi(receptor="SSTR4", iptm=0.944, sst14_ki_nm=1.6, predicted_ki="≥ 5 nM"),
            PredictedKi(receptor="SSTR5", iptm=0.818, sst14_ki_nm=0.3, predicted_ki="≥ 10 nM"),
        ],
        reagents=[
            Reagent(name="cand03",            spec="14aa · Cys SS bond · ≥95% (HPLC) · 5 mg",  vendor="Peptron",       unit_price_krw=2_500_000, qty=1, lead_days="10–14"),
            Reagent(name="Scrambled cand03",  spec="음성대조 · 동일 조성 · 2 mg",              vendor="Peptron",       unit_price_krw=1_200_000, qty=1, lead_days="10"),
            Reagent(name="var12 (D-Thr12)",   spec="stability 보강 · 3 mg",                    vendor="Peptron",       unit_price_krw=1_200_000, qty=1, lead_days="14"),
            Reagent(name="¹²⁵I-Tyr¹¹ SS-14",  spec="radioligand · 0.5 mCi",                    vendor="Perkin-Elmer",  unit_price_krw=4_500_000, qty=1, lead_days="7–10"),
            Reagent(name="SSTR1–5 세포주",     spec="CHO/HEK stable transfected · 5 strain",   vendor="ATCC",          unit_price_krw=800_000,   qty=5, lead_days="5"),
        ],
        protocol=WetlabProtocol(
            format="96-well competition binding",
            tracer="¹²⁵I-Tyr¹¹ SS-14 · 0.05 nM final",
            membrane="SSTR1–5 stable cell, 2 µg/well",
            concentration_range="10⁻¹² – 10⁻⁵ M · 11-point",
            replicates="n = 3 technical × 3 biological",
            negative_control="Scrambled cand03 @ 1 µM",
            readout="γ-counter, 1 min/well",
            analysis="GraphPad Prism · log Ki + Welch t-test",
        ),
        acceptance_criteria=[
            AcceptanceCriterion(criterion="cand03 Ki(SSTR2) < 10 nM"),
            AcceptanceCriterion(criterion="log SI(SSTR1/SSTR2) > 1.0"),
            AcceptanceCriterion(criterion="Tracer Kd 일치 within 2×"),
            AcceptanceCriterion(criterion="Scrambled 억제율 < 10% @ 1 µM"),
            AcceptanceCriterion(criterion="CV (replicate) < 20%"),
        ],
        timeline=[
            TimelineEntry(week="1주",   task="PO 발주 · 시약 입하 추적",          actor="연구원"),
            TimelineEntry(week="2–3주", task="cand03 + scrambled + var12 합성",   actor="Peptron"),
            TimelineEntry(week="3주",   task="QC · HPLC · MS · Ellman SS bond",   actor="화학팀"),
            TimelineEntry(week="4주",   task="SSTR1–5 세포 배양 · membrane 추출", actor="biology"),
            TimelineEntry(week="5–6주", task="Pilot Kd binding (n=1)",            actor="biology"),
            TimelineEntry(week="6–7주", task="Full competition (n=3 × 3 biol)",   actor="biology"),
            TimelineEntry(week="8주",   task="Ki 계산 · 통계 · 보고서",            actor="data"),
        ],
    ).model_dump(mode="json")


# ─────────────────────────────────────────────────────────────────────────────
@router.get("/orders", response_model=WetlabOrderListResponse)
def list_orders() -> WetlabOrderListResponse:
    orders = _load_orders()
    return WetlabOrderListResponse(orders=[
        WetlabOrderListItem(
            id=o["id"],
            candidate_id=o["candidate_id"],
            stage=o["stage"],
            total_krw=o["total_krw"],
            lead_weeks=o["lead_weeks"],
            requested_by=o["requested_by"],
            created_at=o["created_at"],
        ) for o in orders
    ])


@router.get("/orders/{order_id}", response_model=WetlabOrder)
def get_order(order_id: str) -> WetlabOrder:
    orders = _load_orders()
    for o in orders:
        if o["id"] == order_id:
            return WetlabOrder(**o)
    raise HTTPException(404, f"order {order_id} not found")


@router.post("/orders", response_model=WetlabOrder)
def create_order(candidate_id: str) -> WetlabOrder:
    """현재는 cand03 만 자동 생성 (기 정의 발주서). 추후 후보별 발주 빌더 구현."""
    if candidate_id != "cand03":
        raise HTTPException(400, "현재 cand03 발주만 지원 — 다른 후보는 wetlab 팀에 문의")
    orders = _load_orders()
    new_order = _build_cand03_order()
    new_order["id"] = f"WO-{datetime.now(KST).strftime('%Y-%m-%d')}-{len(orders)+1:03d}"
    new_order["created_at"] = datetime.now(KST).isoformat()
    new_order["stage"] = "draft"
    orders.append(new_order)
    _save_orders(orders)
    return WetlabOrder(**new_order)


@router.post("/orders/{order_id}/transition", response_model=WetlabOrder)
def transition_order(order_id: str, req: WetlabTransitionRequest) -> WetlabOrder:
    """상태 머신 검증 — draft → review → approval → PO → shipped 만 허용."""
    flow: list[WetlabStage] = ["draft", "review", "approval", "PO", "shipped"]
    orders = _load_orders()
    for o in orders:
        if o["id"] != order_id:
            continue
        cur = o["stage"]
        if req.to_stage not in flow:
            raise HTTPException(400, f"invalid stage {req.to_stage}")
        if flow.index(req.to_stage) != flow.index(cur) + 1:
            raise HTTPException(400, f"cannot jump {cur} → {req.to_stage} (must advance one step)")
        o["stage"] = req.to_stage
        _save_orders(orders)
        return WetlabOrder(**o)
    raise HTTPException(404, f"order {order_id} not found")
