"""최종 4-Round 종합 보고서 생성기.

Round 1: 모든 chain + MinMover
Round 2: GPCR chain only + MinMover
A1:      GPCR chain only + FlexPepDock (nstruct=10)
A2:      GPCR chain only + Pharmacophore alignment + MinMover (nstruct=5)
"""
import json
from pathlib import Path
from datetime import datetime


SST14_KI = {"SSTR1": 0.4, "SSTR2": 0.2, "SSTR3": 0.8, "SSTR4": 1.6, "SSTR5": 0.3}


def load(path):
    return json.load(open(path)) if Path(path).exists() else []


def organize(data):
    by = {}
    for r in data:
        cid = r.get("candidate_id", "?")
        rname = r.get("receptor", "?")
        by.setdefault(cid, {})[rname] = {
            "ddg": r.get("ddg"),
            "dsasa": r.get("best_dsasa", 0),
            "error": r.get("error"),
        }
    return by


def stats(data):
    total = len(data)
    neg = sum(1 for r in data if r.get("ddg") is not None and r["ddg"] < 0)
    pos = sum(1 for r in data if r.get("ddg") is not None and r["ddg"] > 0)
    zero = sum(1 for r in data if r.get("ddg") is not None and abs(r["ddg"]) < 0.01)
    none = sum(1 for r in data if r.get("ddg") is None)
    return {"total": total, "neg": neg, "pos": pos, "zero": zero, "none": none}


def main():
    base = Path("runs_local/selectivity_demo_20260511")

    r1 = load(base / "pyrosetta_batch" / "all_results.json")
    r2 = load(base / "pyrosetta_batch_v2" / "all_results.json")
    a1 = load(base / "approach1_flexpep" / "all_results.json")
    a2 = load(base / "approach2_pharma" / "all_results.json")

    s1, s2, sa1, sa2 = stats(r1), stats(r2), stats(a1), stats(a2)
    o1, o2, oa1, oa2 = organize(r1), organize(r2), organize(a1), organize(a2)

    # SST-14 wild (cand04) 비교
    def get_sst14(o):
        for cid in o:
            if cid.startswith("cand04_"):
                return o[cid]
        return {}

    sst1, sst2, ssta1, ssta2 = get_sst14(o1), get_sst14(o2), get_sst14(oa1), get_sst14(oa2)

    receptors = ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]

    def fmt_ddg(v):
        if v is None:
            return '<span class="na">—</span>'
        if v < -5:
            return f'<span class="strong-neg">{v:.1f}</span>'
        if v < 0:
            return f'<span class="weak-neg">{v:.2f}</span>'
        if abs(v) < 0.01:
            return f'<span class="zero">0.0</span>'
        if v < 100:
            return f'<span class="weak-pos">{v:.1f}</span>'
        return f'<span class="strong-pos">{v:.0f}</span>'

    sst14_rows = []
    for r in receptors:
        sst14_rows.append(f"""
        <tr>
            <td><strong>{r}</strong></td>
            <td>{SST14_KI[r]} nM</td>
            <td>{fmt_ddg(sst1.get(r, {}).get("ddg"))}</td>
            <td>{fmt_ddg(sst2.get(r, {}).get("ddg"))}</td>
            <td>{fmt_ddg(ssta1.get(r, {}).get("ddg"))}</td>
            <td>{fmt_ddg(ssta2.get(r, {}).get("ddg"))}</td>
        </tr>""")

    # 4-Round 통계 표
    stats_rows = f"""
        <tr><td><strong>Round 1</strong></td><td>모든 chain + MinMover</td><td>3</td><td>{s1['neg']}</td><td>{s1['pos']}</td><td>{s1['none']}</td></tr>
        <tr><td><strong>Round 2</strong></td><td>GPCR chain only + MinMover</td><td>3</td><td>{s2['neg']}</td><td>{s2['pos']}</td><td>{s2['none']}</td></tr>
        <tr><td><strong>A1</strong></td><td>GPCR + FlexPepDock</td><td>10</td><td>{sa1['neg']}</td><td>{sa1['pos']}</td><td>{sa1['none']}</td></tr>
        <tr><td><strong>A2</strong></td><td>GPCR + Pharmacophore align</td><td>5</td><td>{sa2['neg']}</td><td>{sa2['pos']}</td><td>{sa2['none']}</td></tr>
    """

    html = f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8">
<title>SST-14 Selectivity 최종 보고서 — 2026-05-11</title>
<style>
  body {{ font-family: -apple-system,"Segoe UI",sans-serif; background:#0d1117; color:#c9d1d9; margin:0; padding:24px; }}
  h1, h2, h3 {{ color:#58a6ff; border-bottom:1px solid #30363d; padding-bottom:8px; }}
  h2 {{ margin-top:32px; color:#79c0ff; }}
  h3 {{ color:#d29922; border-bottom:none; margin-top:24px; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; font-size:13px; }}
  th, td {{ padding:8px 12px; border-bottom:1px solid #30363d; text-align:center; }}
  th {{ background:#161b22; color:#79c0ff; font-size:11px; text-transform:uppercase; }}
  td.left {{ text-align:left; }}
  .strong-neg {{ color:#3fb950; font-weight:bold; }}
  .weak-neg {{ color:#56d364; }}
  .zero {{ color:#8b949e; }}
  .weak-pos {{ color:#d29922; }}
  .strong-pos {{ color:#f85149; font-weight:bold; }}
  .na {{ color:#6e7681; font-style:italic; }}
  .summary {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:24px; margin:16px 0; }}
  .kpi {{ display:inline-block; margin-right:32px; }}
  .kpi-label {{ color:#8b949e; font-size:12px; text-transform:uppercase; }}
  .kpi-value {{ color:#58a6ff; font-size:24px; font-weight:bold; }}
  .warning {{ background:#3d1015; border-left:4px solid #f85149; padding:12px 16px; border-radius:4px; margin:16px 0; }}
  .info {{ background:#1d2c3d; border-left:4px solid #58a6ff; padding:12px 16px; border-radius:4px; margin:16px 0; }}
  .success {{ background:#0d3320; border-left:4px solid #3fb950; padding:12px 16px; border-radius:4px; margin:16px 0; }}
  code {{ background:#161b22; padding:2px 6px; border-radius:3px; font-size:12px; }}
  .footer {{ color:#6e7681; font-size:12px; margin-top:48px; padding-top:16px; border-top:1px solid #30363d; }}
  ul {{ line-height:1.8; }}
</style></head><body>

<h1>SST-14 Selectivity 분석 — 최종 보고서</h1>
<div style="color:#8b949e;">작성: {datetime.now().strftime('%Y-%m-%d %H:%M')} · 4가지 도킹 전략 × 10 후보 × 5 수용체 = <strong>200 페어</strong></div>

<h2>핵심 결론</h2>
<div class="warning">
  <strong>본 환경에서 PyRosetta 단독으로 SSTR-펩타이드 selectivity 도킹은 불가능한 것으로 판명되었습니다.</strong>
  4가지 변형 전략 모두 SST-14 wild type조차 SSTR2 결합을 재현하지 못함 (모든 결과 양수 또는 잘못된 noise interface).
  GPCR 결정 구조의 closed pocket + receptor backbone rigidity가 핵심 장애.
</div>

<h2>4가지 도킹 전략 비교</h2>
<table>
  <tr><th>전략</th><th>방법</th><th>nstruct</th><th>음수 결합</th><th>양수 clash</th><th>실패</th></tr>
  {stats_rows}
</table>

<h2>SST-14 Wild Type (cand04_AGCKNFFWKTFTSC) — 정량 비교</h2>
<div class="info">
  실측 Ki (nM): SST-14는 SSTR1-5 모두에 sub-nM ~ 수 nM 친화도. <strong>SSTR2가 0.2 nM로 최강.</strong>
  성공한 도킹은 모든 수용체에서 음수 ddG가 나와야 하고, SSTR2가 가장 음수 (가장 강결합)여야 함.
</div>
<table>
  <tr><th>수용체</th><th>실측 Ki</th><th>Round 1</th><th>Round 2</th><th>A1 (FlexPep)</th><th>A2 (Pharma)</th></tr>
  {"".join(sst14_rows)}
</table>

<h3>관찰</h3>
<ul>
  <li><strong>Round 1</strong>: SSTR1만 음수 (-162) → 사실은 G-protein/scFv noise chain과의 interface (잘못된 음수)</li>
  <li><strong>Round 2</strong>: noise chain 제거 후 모든 receptor 양수 → noise 없이는 진짜 binding 없음</li>
  <li><strong>A1 FlexPepDock</strong>: lowres+highres 적용해도 모두 양수 (16K-29K) → backbone freedom으로도 pocket 진입 실패</li>
  <li><strong>A2 Pharmacophore</strong>: NFFWKT만 NCAA에 정렬 후 MinMover → pocket 깊이 정렬 차이로 clash</li>
</ul>

<h2>원인 분석</h2>
<div class="warning">
<strong>1. GPCR 결정 구조의 closed conformation</strong><br>
SSTR1/2/3/4/5 모두 결합된 NCAA peptoid/소분자 ligand와 함께 결정화. 그 ligand가 pocket을 점유 → 우리가 ligand 좌표를 추출한 후 그 자리에 14aa 펩타이드를 넣으려 해도, receptor side-chain이 small ligand에 맞춰 닫혀 있어 큰 펩타이드가 들어가지 못함.

<strong>2. FlexPepDock의 limitation</strong><br>
FlexPepDock은 peptide만 flexible. Receptor backbone과 sidechain은 대부분 rigid. GPCR의 binding pocket entry는 receptor TM helix가 펩타이드 진입을 위해 약간 열려야 하는데 그 conformational change를 sampling 불가.

<strong>3. fa_standard scorefxn 한계</strong><br>
PyRosetta 본 보고서: "fa_standard은 상대 순위 참고용, 절대값 해석 주의". 실제로 절대값이 의미 있을 수준이 안 됨.
</div>

<h2>전체 후보 × 수용체 매트릭스 (A1 — 가장 정교한 시도)</h2>
{render_matrix(oa1, receptors)}

<h2>실행 가능한 다음 단계</h2>
<div class="success">
<strong>옵션 A — Boltz-2 사용 (sysadmin 허용 후)</strong><br>
<code>api.colabfold.com</code> 화이트리스트 추가 후 본 50쌍 재실행. AlphaFold-Multimer 수준 정확도, MSA 기반 co-evolution + GPU 추론. 페어당 1-3분. 요청서: <code>docs/sysadmin_request_colabfold.md</code> 제출 완료.

<strong>옵션 B — HADDOCK 로컬 설치 (CNS 라이센스 필요)</strong><br>
GPCR-peptide induced fit 도킹 가능. 설치 + DB 빌드 시간 비용 큼 (~수일).

<strong>옵션 C — apo (ligand-free) 수용체 구조 별도 준비</strong><br>
수동 정제로 ligand 제거 + open conformation 모델 빌드. SSTR2 active state apo 모델은 SwissModel/AlphaFoldDB 가능성.

<strong>옵션 D — Receptor backbone relax 추가</strong><br>
도킹 전 receptor 자체를 FastRelax (CCD-relax-style)으로 pocket 열기. 그러나 자연 conformation 유지 보장 안 됨.
</div>

<h2>현재 결과의 활용 가치</h2>
<ul>
  <li>본 보고서의 ddG 값은 selectivity 판단에 사용할 수 없음 (실측 Ki와 불일치)</li>
  <li><strong>SAR 데이터로는 활용 가능</strong>: 10 후보의 상대적 clash 정도 차이 → 어느 위치 변이가 결합 affinity에 영향 큰지 간접 지표</li>
  <li>방법론 검증 측면: PyRosetta로는 GPCR-peptide docking 부적합함이 명확해짐 → 다음 단계 도구 선택의 근거</li>
</ul>

<h2>참고 리소스</h2>
<ul>
  <li>원시 결과: <code>runs_local/selectivity_demo_20260511/{{pyrosetta_batch, pyrosetta_batch_v2, approach1_flexpep, approach2_pharma}}/all_results.json</code></li>
  <li>구조 데이터: <code>data/somatostatin_receptor/SSTR{{1-5}}_*.cif</code></li>
  <li>리모트 production 보고서: <code>docs/presentation/01_appendix/selectivity_docking_report.md</code></li>
  <li>sysadmin 요청: <code>docs/sysadmin_request_colabfold.md</code></li>
  <li>실험 후보 출처: <code>runs/pyrosetta_flow/archives/sst14_mutdock_*_dashboard.json</code> (539 후보 → unique 333 → top 10)</li>
</ul>

<div class="footer">
Generated by <code>generate_final_report.py</code> · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>

</body></html>"""

    out_path = base / "report_final.html"
    out_path.write_text(html)
    print(f"Final report: {out_path}")

    summary = {
        "rounds": {
            "round1": s1, "round2": s2, "a1_flexpep": sa1, "a2_pharma": sa2,
        },
        "sst14_wild": {
            "round1": {r: sst1.get(r, {}).get("ddg") for r in receptors},
            "round2": {r: sst2.get(r, {}).get("ddg") for r in receptors},
            "a1": {r: ssta1.get(r, {}).get("ddg") for r in receptors},
            "a2": {r: ssta2.get(r, {}).get("ddg") for r in receptors},
            "ki_nm": SST14_KI,
        },
        "conclusion": "PyRosetta 단독으로 SSTR-펩타이드 selectivity 도킹 불가",
        "next_steps": ["Boltz-2 (sysadmin 허용 필요)", "HADDOCK 설치", "apo receptor 구조 준비", "Receptor relax 추가"],
    }
    summary_path = base / "final_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str, ensure_ascii=False))
    print(f"Summary JSON: {summary_path}")


def render_matrix(o, receptors):
    rows = []
    for cid in sorted(o.keys()):
        cells = []
        seq = cid.split("_", 1)[-1] if "_" in cid else cid
        for r in receptors:
            v = o[cid].get(r, {}).get("ddg")
            if v is None:
                cells.append('<td><span class="na">—</span></td>')
            elif v < -5:
                cells.append(f'<td><span class="strong-neg">{v:.1f}</span></td>')
            elif v < 0:
                cells.append(f'<td><span class="weak-neg">{v:.2f}</span></td>')
            elif abs(v) < 0.01:
                cells.append('<td><span class="zero">0.0</span></td>')
            elif v < 100:
                cells.append(f'<td><span class="weak-pos">{v:.1f}</span></td>')
            else:
                cells.append(f'<td><span class="strong-pos">{v:.0f}</span></td>')
        rows.append(f"<tr><td class='left'>{cid[:8]}</td><td class='left'>{seq}</td>{''.join(cells)}</tr>")
    return f"""<table>
  <tr><th>ID</th><th>서열</th><th>SSTR1</th><th>SSTR2</th><th>SSTR3</th><th>SSTR4</th><th>SSTR5</th></tr>
  {"".join(rows)}
</table>"""


if __name__ == "__main__":
    main()
