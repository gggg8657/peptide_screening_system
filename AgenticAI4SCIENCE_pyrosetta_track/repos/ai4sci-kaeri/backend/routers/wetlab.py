"""Wetlab order router backed by a small local JSON store."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException

from ..schemas.dashboard import (
    AcceptanceCriterion,
    PredictedKi,
    Reagent,
    TimelineEntry,
    WetlabOrder,
    WetlabOrderListItem,
    WetlabOrderListResponse,
    WetlabProtocol,
    WetlabStage,
    WetlabTransitionRequest,
)

router = APIRouter()
KST = timezone(timedelta(hours=9))
FLOW: list[WetlabStage] = ["draft", "submitted", "approved", "shipped", "returned"]
PRST_SYNTHESIS_STATE = "queued_for_synthesis"
PRST_CANDIDATES = [
    {
        "id": "WO-2026-PRST-001",
        "candidate_id": "PRST-001",
        "sequence": "AGCKNIIWKTITSC",
        "predicted_ddg": -10.5,
        "predicted_dg": -105.5,
        "admet_tox": 1.0,
        "selectivity": 250.0,
        "tier": "S",
        "radiolysis_count": 1,
        "instability_index": 28.5,
        "predicted_ki_sstr2": "0.5-5 nM",
    },
    {
        "id": "WO-2026-PRST-002",
        "candidate_id": "PRST-002",
        "sequence": "AGCKNFIWKTITSC",
        "predicted_ddg": -6.8,
        "predicted_dg": -101.8,
        "admet_tox": 1.0,
        "selectivity": 180.0,
        "tier": "B",
        "radiolysis_count": 2,
        "instability_index": 30.1,
        "predicted_ki_sstr2": "0.5-5 nM",
    },
    {
        "id": "WO-2026-PRST-003",
        "candidate_id": "PRST-003",
        "sequence": "AGCRNFIWKTITSC",
        "predicted_ddg": -4.2,
        "predicted_dg": -99.2,
        "admet_tox": 1.0,
        "selectivity": 130.0,
        "tier": "B",
        "radiolysis_count": 2,
        "instability_index": 35.0,
        "predicted_ki_sstr2": "1-10 nM",
    },
    {
        "id": "WO-2026-PRST-004",
        "candidate_id": "PRST-004",
        "sequence": "AICKNFIWKTITSC",
        "predicted_ddg": -5.0,
        "predicted_dg": -100.0,
        "admet_tox": 1.0,
        "selectivity": 200.0,
        "tier": "B",
        "radiolysis_count": 2,
        "instability_index": 32.0,
        "predicted_ki_sstr2": "1-5 nM",
    },
]


class OrderListPayload(dict):
    def model_dump(self) -> dict:
        return dict(self)


def _orders_store() -> Path:
    return Path(__file__).resolve().parents[5] / "runs_local" / "wetlab_orders.json"


def _save_orders(orders: list[dict]) -> None:
    store = _orders_store()
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("w", encoding="utf-8") as handle:
        json.dump(orders, handle, ensure_ascii=False, indent=2)


def _build_generic_order(
    candidate_id: str,
    candidate_seq: str,
    flexpepdock_job_id: str | None = None,
) -> dict:
    """임의 candidate_id/sequence에 대한 placeholder order 생성 (Manual Selectivity 연동)."""
    is_cand03 = candidate_id == "cand03"
    return WetlabOrder(
        id=f"WO-{datetime.now(KST).strftime('%Y-%m-%d')}-XXX",
        candidate_id=candidate_id,
        candidate_seq=candidate_seq,
        stage="draft",
        total_krw=13_400_000 if is_cand03 else 9_500_000,
        lead_weeks=8,
        requested_by="dongjukim@kaeri.re.kr",
        created_at=datetime.now(KST),
        flexpepdock_job_id=flexpepdock_job_id,
        hypothesis={
            "h1": (
                f"{candidate_id}은 SSTR2에 대해 SST-14 대비 향상된 선택성을 보이며 "
                "Ki(SSTR2) < 10 nM, log(Ki(SSTR1)/Ki(SSTR2)) > 1.0"
            ),
            "h0": (
                f"{candidate_id}의 5개 SSTR Ki 프로파일이 SST-14와 "
                "통계적으로 유의미한 차이가 없다 (ANOVA p > 0.05)"
            ),
        },
        predicted_ki=[
            PredictedKi(receptor="SSTR1", iptm=0.0, sst14_ki_nm=0.4, predicted_ki="TBD (Manual Selectivity 결과 기반)"),
            PredictedKi(receptor="SSTR2", iptm=0.0, sst14_ki_nm=0.2, predicted_ki="TBD", target=True),
            PredictedKi(receptor="SSTR3", iptm=0.0, sst14_ki_nm=0.8, predicted_ki="TBD"),
            PredictedKi(receptor="SSTR4", iptm=0.0, sst14_ki_nm=1.6, predicted_ki="TBD"),
            PredictedKi(receptor="SSTR5", iptm=0.0, sst14_ki_nm=0.3, predicted_ki="TBD"),
        ],
        reagents=[
            Reagent(name=candidate_id, spec="14aa · Cys SS bond · ≥95% (HPLC) · 5 mg", vendor="Peptron", unit_price_krw=2_500_000, qty=1, lead_days="10–14"),
            Reagent(name=f"Scrambled {candidate_id}", spec="음성대조 · 동일 조성 · 2 mg", vendor="Peptron", unit_price_krw=1_200_000, qty=1, lead_days="10"),
            Reagent(name="¹²⁵I-Tyr¹¹ SS-14", spec="radioligand · 0.5 mCi", vendor="Perkin-Elmer", unit_price_krw=4_500_000, qty=1, lead_days="7–10"),
            Reagent(name="SSTR1–5 세포주", spec="CHO/HEK stable transfected · 5 strain", vendor="ATCC", unit_price_krw=800_000, qty=5, lead_days="5"),
        ],
        protocol=WetlabProtocol(
            format="96-well competition binding",
            tracer="¹²⁵I-Tyr¹¹ SS-14 · 0.05 nM final",
            membrane="SSTR1–5 stable cell, 2 µg/well",
            concentration_range="10⁻¹² – 10⁻⁵ M · 11-point",
            replicates="n = 3 technical × 3 biological",
            negative_control=f"Scrambled {candidate_id} @ 1 µM",
            readout="γ-counter, 1 min/well",
            analysis="GraphPad Prism · log Ki + Welch t-test",
        ),
        acceptance_criteria=[
            AcceptanceCriterion(criterion=f"{candidate_id} Ki(SSTR2) < 10 nM"),
            AcceptanceCriterion(criterion="log SI(SSTR1/SSTR2) > 1.0"),
            AcceptanceCriterion(criterion="Tracer Kd 일치 within 2×"),
            AcceptanceCriterion(criterion="Scrambled 억제율 < 10% @ 1 µM"),
            AcceptanceCriterion(criterion="CV (replicate) < 20%"),
        ],
        timeline=[
            TimelineEntry(week="1주", task="PO 발주 · 시약 입하 추적", actor="연구원"),
            TimelineEntry(week="2–3주", task=f"{candidate_id} + scrambled 합성", actor="Peptron"),
            TimelineEntry(week="3주", task="QC · HPLC · MS · Ellman SS bond", actor="화학팀"),
            TimelineEntry(week="4주", task="SSTR1–5 세포 배양 · membrane 추출", actor="biology"),
            TimelineEntry(week="5–6주", task="Pilot Kd binding (n=1)", actor="biology"),
            TimelineEntry(week="6–7주", task="Full competition (n=3 × 3 biol)", actor="biology"),
            TimelineEntry(week="8주", task="Ki 계산 · 통계 · 보고서", actor="data"),
        ],
    ).model_dump(mode="json")


def _build_cand03_order() -> dict:
    return WetlabOrder(
        id="WO-2026-005",
        candidate_id="cand03",
        candidate_seq="AICKNFFWKTFTSC",
        stage="approved",
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
            Reagent(name="cand03", spec="14aa · Cys SS bond · ≥95% (HPLC) · 5 mg", vendor="Peptron", unit_price_krw=2_500_000, qty=1, lead_days="10–14"),
            Reagent(name="Scrambled cand03", spec="음성대조 · 동일 조성 · 2 mg", vendor="Peptron", unit_price_krw=1_200_000, qty=1, lead_days="10"),
            Reagent(name="var12 (D-Thr12)", spec="stability 보강 · 3 mg", vendor="Peptron", unit_price_krw=1_200_000, qty=1, lead_days="14"),
            Reagent(name="¹²⁵I-Tyr¹¹ SS-14", spec="radioligand · 0.5 mCi", vendor="Perkin-Elmer", unit_price_krw=4_500_000, qty=1, lead_days="7–10"),
            Reagent(name="SSTR1–5 세포주", spec="CHO/HEK stable transfected · 5 strain", vendor="ATCC", unit_price_krw=800_000, qty=5, lead_days="5"),
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
            TimelineEntry(week="1주", task="PO 발주 · 시약 입하 추적", actor="연구원"),
            TimelineEntry(week="2–3주", task="cand03 + scrambled + var12 합성", actor="Peptron"),
            TimelineEntry(week="3주", task="QC · HPLC · MS · Ellman SS bond", actor="화학팀"),
            TimelineEntry(week="4주", task="SSTR1–5 세포 배양 · membrane 추출", actor="biology"),
            TimelineEntry(week="5–6주", task="Pilot Kd binding (n=1)", actor="biology"),
            TimelineEntry(week="6–7주", task="Full competition (n=3 × 3 biol)", actor="biology"),
            TimelineEntry(week="8주", task="Ki 계산 · 통계 · 보고서", actor="data"),
        ],
    ).model_dump(mode="json")


def _build_prst_order(candidate: dict) -> dict:
    candidate_id = candidate["candidate_id"]
    order = _build_generic_order(
        candidate_id=candidate_id,
        candidate_seq=candidate["sequence"],
    )
    order.update(
        {
            "id": candidate["id"],
            "candidate_id": candidate_id,
            "candidate_seq": candidate["sequence"],
            "sequence": candidate["sequence"],
            "stage": "submitted",
            "state": PRST_SYNTHESIS_STATE,
            "created_at": datetime(2026, 5, 20, 9, 0, tzinfo=KST).isoformat(),
            "predicted_ddg": candidate["predicted_ddg"],
            "predicted_dg": candidate["predicted_dg"],
            "admet_tox": candidate["admet_tox"],
            "selectivity": candidate["selectivity"],
            "tier": candidate["tier"],
            "radiolysis_count": candidate["radiolysis_count"],
            "instability_index": candidate["instability_index"],
            "total_krw": 12_000_000,
            "lead_weeks": 8,
            "hypothesis": {
                "h1": (
                    f"{candidate_id}는 SSTR2 Ki < 10 nM 및 177Lu 72h RCP >= 90%를 "
                    "wet-lab에서 달성한다."
                ),
                "h0": f"{candidate_id}의 Ki(SSTR2) 및 5-SSTR 프로파일이 SST-14와 유의미한 차이가 없다.",
            },
            "predicted_ki": [
                PredictedKi(receptor="SSTR1", iptm=0.0, sst14_ki_nm=0.4, predicted_ki=">= 5 nM"),
                PredictedKi(
                    receptor="SSTR2",
                    iptm=0.0,
                    sst14_ki_nm=0.2,
                    predicted_ki=candidate["predicted_ki_sstr2"],
                    target=True,
                ),
                PredictedKi(receptor="SSTR3", iptm=0.0, sst14_ki_nm=0.8, predicted_ki=">= 10 nM"),
                PredictedKi(receptor="SSTR4", iptm=0.0, sst14_ki_nm=1.6, predicted_ki=">= 5 nM"),
                PredictedKi(receptor="SSTR5", iptm=0.0, sst14_ki_nm=0.3, predicted_ki=">= 10 nM"),
            ],
            "acceptance_criteria": [
                AcceptanceCriterion(criterion="합성 순도 >= 95% HPLC").model_dump(mode="json"),
                AcceptanceCriterion(criterion="SS bond 고리화 Ellman's test 통과").model_dump(mode="json"),
                AcceptanceCriterion(criterion="177Lu 표지 직후 RCP >= 95% ITLC").model_dump(mode="json"),
                AcceptanceCriterion(criterion="177Lu 72h RCP >= 90%").model_dump(mode="json"),
                AcceptanceCriterion(criterion="Ki(SSTR2) < 10 nM").model_dump(mode="json"),
                AcceptanceCriterion(criterion="log SI(SSTR1/SSTR2) > 1.0").model_dump(mode="json"),
            ],
        }
    )
    order["predicted_ki"] = [ki.model_dump(mode="json") if hasattr(ki, "model_dump") else ki for ki in order["predicted_ki"]]
    order["reagents"][0]["name"] = candidate_id
    order["reagents"][0]["spec"] = "14aa · Cys SS bond · DOTA 협의 · >=95% (HPLC) · 5-10 mg"
    order["reagents"][1]["name"] = f"Scrambled {candidate_id}"
    return order


def _build_prst_orders() -> list[dict]:
    return [_build_prst_order(candidate) for candidate in PRST_CANDIDATES]


def _seed_orders() -> list[dict]:
    orders = [_build_cand03_order(), *_build_prst_orders()]
    _save_orders(orders)
    return orders


def _merge_builtin_orders(orders: list[dict]) -> tuple[list[dict], bool]:
    by_id = {order.get("id"): order for order in orders}
    changed = False
    for prst_order in _build_prst_orders():
        existing = by_id.get(prst_order["id"])
        if existing is None:
            orders.append(prst_order)
            changed = True
            continue
        for key in ("sequence", "state", "predicted_ddg", "predicted_dg", "admet_tox", "selectivity", "tier"):
            if existing.get(key) != prst_order[key]:
                existing[key] = prst_order[key]
                changed = True
    return orders, changed


def _load_orders() -> list[dict]:
    store = _orders_store()
    if not store.exists():
        return _seed_orders()
    with store.open("r", encoding="utf-8") as handle:
        orders = json.load(handle)
    changed = False
    for order in orders:
        stage = order.get("stage")
        if stage == "review":
            order["stage"] = "submitted"
            changed = True
        elif stage == "approval":
            order["stage"] = "approved"
            changed = True
        elif stage == "PO":
            order["stage"] = "shipped"
            changed = True
    orders, builtins_changed = _merge_builtin_orders(orders)
    changed = changed or builtins_changed
    if changed:
        _save_orders(orders)
    return orders


@router.get("/orders")
def list_orders() -> dict:
    orders = _load_orders()
    return OrderListPayload({
        "orders": [
            {
                "id": order["id"],
                "candidate_id": order["candidate_id"],
                "sequence": order.get("sequence") or order.get("candidate_seq"),
                "candidate_seq": order.get("candidate_seq"),
                "predicted_ddg": order.get("predicted_ddg"),
                "admet_tox": order.get("admet_tox"),
                "state": order.get("state") or order.get("stage"),
                "stage": order["stage"],
                "total_krw": order["total_krw"],
                "lead_weeks": order["lead_weeks"],
                "requested_by": order["requested_by"],
                "created_at": order["created_at"],
            }
            for order in orders
        ]
    })


@router.get("/orders/{order_id}", response_model=WetlabOrder)
def get_order(order_id: str) -> WetlabOrder:
    for order in _load_orders():
        if order["id"] == order_id:
            return WetlabOrder(**order)
    raise HTTPException(status_code=404, detail=f"order {order_id} not found")


@router.post("/orders", response_model=WetlabOrder)
def create_order(payload: dict = Body(...)) -> WetlabOrder:
    candidate_id = str(payload.get("candidate_id", "")).strip()
    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id 필수")

    candidate_seq = str(payload.get("candidate_seq", "")).strip().upper()
    flexpepdock_job_id = payload.get("flexpepdock_job_id")
    flexpepdock_job_id_str = str(flexpepdock_job_id) if flexpepdock_job_id else None

    orders = _load_orders()

    if candidate_id == "cand03":
        # 레거시: hardcoded cand03 order 보존 (h0/h1, reagents 등 cand03 특화)
        new_order = _build_cand03_order()
        new_order["stage"] = "draft"
    else:
        # Manual Selectivity 연동: 임의 sequence → placeholder order
        # candidate_seq 누락 시 candidate_id를 sequence로 가정 (대문자화)
        seq = candidate_seq or candidate_id.upper()
        new_order = _build_generic_order(
            candidate_id=candidate_id,
            candidate_seq=seq,
            flexpepdock_job_id=flexpepdock_job_id_str,
        )

    new_order["id"] = f"WO-{datetime.now(KST).strftime('%Y-%m-%d')}-{len(orders) + 1:03d}"
    new_order["created_at"] = datetime.now(KST).isoformat()
    if flexpepdock_job_id_str:
        new_order["flexpepdock_job_id"] = flexpepdock_job_id_str

    orders.append(new_order)
    _save_orders(orders)
    return WetlabOrder(**new_order)


@router.post("/orders/{order_id}/transition", response_model=WetlabOrder)
def transition_order(order_id: str, req: WetlabTransitionRequest) -> WetlabOrder:
    orders = _load_orders()
    for order in orders:
        if order["id"] != order_id:
            continue
        current = order["stage"]
        if FLOW.index(req.to_stage) != FLOW.index(current) + 1:
            raise HTTPException(status_code=400, detail=f"cannot jump {current} → {req.to_stage}")
        order["stage"] = req.to_stage
        _save_orders(orders)
        return WetlabOrder(**order)
    raise HTTPException(status_code=404, detail=f"order {order_id} not found")
