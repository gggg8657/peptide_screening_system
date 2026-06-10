"""3-도구 selectivity 분석 보고서 HTML 자동 생성기.

입력:
  - runs_local/selectivity_demo_20260511/pyrosetta_batch/all_results.json (10 후보 × 5 receptor)
  - runs_local/selectivity_demo_20260511/top10_candidates.json
  - runs_local/selectivity_demo_20260511/receptor_manifest.json

출력:
  - runs_local/selectivity_demo_20260511/report.html — 인터랙티브 보고서
"""
import json
from pathlib import Path
from datetime import datetime


# 실측 Ki (nM) — selectivity 평가 ground truth
# 참고: Patel YC. (1999) Front Neuroendocrinol; Hoyer D. et al. (1995)
# SST-14의 SSTR1-5 결합 Ki 값. 같은 수용체에 대한 변이체는 unknown.
SST14_KI = {
    "SSTR1": 0.4,
    "SSTR2": 0.2,
    "SSTR3": 0.8,
    "SSTR4": 1.6,
    "SSTR5": 0.3,
}


def load_results(base_dir: Path, batch_subdir: str = "pyrosetta_batch", manifest_name: str = "receptor_manifest.json"):
    """모든 입력 데이터 로드."""
    with open(base_dir / batch_subdir / "all_results.json") as f:
        pyrosetta_results = json.load(f)
    with open(base_dir / "top10_candidates.json") as f:
        candidates = json.load(f)
    with open(base_dir / manifest_name) as f:
        receptors = json.load(f)
    return pyrosetta_results, candidates, receptors


def organize_by_candidate(results):
    """후보별 결과 dict (cid → receptor → ddg)."""
    by_cand = {}
    for r in results:
        cid = r.get("candidate_id", "?")
        rname = r.get("receptor", "?")
        ddg = r.get("ddg")
        by_cand.setdefault(cid, {})[rname] = {
            "ddg": ddg,
            "dsasa": r.get("best_dsasa", 0),
            "seq": r.get("peptide_seq"),
            "error": r.get("error"),
        }
    return by_cand


def compute_selectivity(per_cand, sstr2_key="SSTR2"):
    """각 후보의 selectivity margin 계산.

    selectivity_margin = SSTR2_ddg - max(offtarget_ddg)
    음수일수록 SSTR2에 더 선택적.
    """
    summary = {}
    for cid, recs in per_cand.items():
        sstr2 = recs.get(sstr2_key, {}).get("ddg")
        offtargets = {}
        for rname, r in recs.items():
            if rname == sstr2_key:
                continue
            if r.get("ddg") is not None:
                offtargets[rname] = r["ddg"]

        margin = None
        worst_off = None
        if sstr2 is not None and offtargets:
            worst_off_name, worst_off_val = max(offtargets.items(), key=lambda x: -x[1])
            worst_off = worst_off_name
            margin = sstr2 - worst_off_val

        # Tier 분류 (selectivity_docking_report.md 기준)
        tier = "T0"
        if margin is not None:
            if margin <= -3.0: tier = "T3"
            elif margin <= -2.0: tier = "T2"
            elif margin <= -1.5: tier = "T1"

        summary[cid] = {
            "seq": next((r["seq"] for r in recs.values() if r.get("seq")), None),
            "sstr2_ddg": sstr2,
            "offtargets": offtargets,
            "worst_offtarget": worst_off,
            "margin": margin,
            "tier": tier,
        }
    return summary


def render_html(per_cand, summary, candidates, receptors):
    """HTML 보고서 생성."""
    sstr5_loaded = bool(receptors.get("SSTR5", {}).get("ncaa_center"))

    # 데이터 테이블 — 행=후보, 열=수용체
    table_rows = []
    sorted_cids = sorted(summary.keys(), key=lambda c: summary[c]["margin"] if summary[c]["margin"] is not None else 999)
    for cid in sorted_cids:
        s = summary[cid]
        seq = s["seq"] or "?"
        cells = []
        for rname in ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]:
            r = per_cand[cid].get(rname, {})
            ddg = r.get("ddg")
            if ddg is None:
                cells.append('<td class="na">NA</td>')
            else:
                cls = "neg" if ddg < -5 else "zero" if abs(ddg) < 0.01 else "pos" if ddg > 0 else "weak"
                cells.append(f'<td class="{cls}">{ddg:.2f}</td>')
        margin_str = f"{s['margin']:.2f}" if s["margin"] is not None else "—"
        tier_class = s["tier"].lower()
        table_rows.append(f"""
        <tr>
            <td class="cid">{cid}</td>
            <td class="seq">{seq}</td>
            {"".join(cells)}
            <td class="margin">{margin_str}</td>
            <td><span class="tier {tier_class}">{s['tier']}</span></td>
        </tr>""")

    # Ground truth 비교 (SST-14만)
    sst14_row = next((s for cid, s in summary.items() if s["seq"] == "AGCKNFFWKTFTSC"), None)
    gt_rows = []
    if sst14_row:
        for rname in ["SSTR1", "SSTR2", "SSTR3", "SSTR4", "SSTR5"]:
            ki = SST14_KI.get(rname)
            expected = "최강" if rname == "SSTR2" else "유사" if ki and ki < 1 else "약함"
            measured = sst14_row.get("offtargets", {}).get(rname) if rname != "SSTR2" else sst14_row.get("sstr2_ddg")
            measured_str = f"{measured:.2f}" if measured is not None else "—"
            match = "✅" if (rname == "SSTR2" and measured is not None and measured < -5) else "❓"
            gt_rows.append(f"<tr><td>{rname}</td><td>{ki} nM</td><td>{expected}</td><td>{measured_str}</td><td>{match}</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8">
<title>SST-14 Selectivity 종합 보고서 — 2026-05-11</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; background:#0d1117; color:#c9d1d9; margin:0; padding:24px; }}
  h1, h2, h3 {{ color:#58a6ff; border-bottom:1px solid #30363d; padding-bottom:8px; }}
  h2 {{ margin-top:32px; color:#79c0ff; }}
  .summary {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:24px; margin:16px 0; }}
  .kpi {{ display:inline-block; margin-right:32px; }}
  .kpi-label {{ color:#8b949e; font-size:12px; text-transform:uppercase; }}
  .kpi-value {{ color:#58a6ff; font-size:28px; font-weight:bold; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; font-size:13px; }}
  th, td {{ padding:8px 12px; border-bottom:1px solid #30363d; text-align:center; }}
  th {{ background:#161b22; color:#79c0ff; font-size:11px; text-transform:uppercase; position:sticky; top:0; }}
  td.cid, td.seq {{ text-align:left; font-family:monospace; font-size:12px; }}
  td.neg {{ color:#3fb950; font-weight:bold; }}
  td.pos {{ color:#f85149; }}
  td.zero {{ color:#8b949e; }}
  td.na {{ color:#6e7681; font-style:italic; }}
  td.weak {{ color:#d29922; }}
  td.margin {{ font-weight:bold; }}
  .tier {{ padding:2px 10px; border-radius:10px; font-size:11px; font-weight:bold; }}
  .tier.t3 {{ background:#0d3320; color:#3fb950; }}
  .tier.t2 {{ background:#1a2c1d; color:#56d364; }}
  .tier.t1 {{ background:#2c2a1a; color:#d29922; }}
  .tier.t0 {{ background:#3d1015; color:#f85149; }}
  .warning {{ background:#3d1015; border-left:4px solid #f85149; padding:12px 16px; border-radius:4px; margin:16px 0; }}
  .info {{ background:#1d2c3d; border-left:4px solid #58a6ff; padding:12px 16px; border-radius:4px; margin:16px 0; }}
  .footer {{ color:#6e7681; font-size:12px; margin-top:48px; padding-top:16px; border-top:1px solid #30363d; }}
  ul {{ line-height:1.8; }}
  code {{ background:#161b22; padding:2px 6px; border-radius:3px; font-size:12px; }}
</style></head><body>

<h1>SST-14 Selectivity 종합 보고서</h1>
<div style="color:#8b949e;">작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} · Pipeline: PyRosetta FlexPepDock + NCAA-anchored placement · 후보 10 × 수용체 5 = 50 도킹 페어</div>

<h2>요약 (KPI)</h2>
<div class="summary">
  <div class="kpi"><div class="kpi-label">도킹 성공</div><div class="kpi-value">{sum(1 for r in per_cand.values() for s in r.values() if s.get('ddg') is not None and s['ddg'] < 0)}/{sum(1 for r in per_cand.values() for _ in r.values())}</div></div>
  <div class="kpi"><div class="kpi-label">T2 이상 Pass</div><div class="kpi-value" style="color:#3fb950">{sum(1 for s in summary.values() if s['tier'] in ('T2','T3'))}</div></div>
  <div class="kpi"><div class="kpi-label">최저 마진</div><div class="kpi-value">{min((s['margin'] for s in summary.values() if s['margin'] is not None), default=0):.2f}</div></div>
  <div class="kpi"><div class="kpi-label">평가 후보</div><div class="kpi-value">{len(summary)}</div></div>
</div>

<h2>도킹 도구별 가용성</h2>
<table>
  <tr><th>도구</th><th>환경</th><th>상태</th><th>비고</th></tr>
  <tr><td>PyRosetta FlexPepDock</td><td>bio-tools</td><td style="color:#3fb950">✅ 가동</td><td>본 보고서의 데이터 소스</td></tr>
  <tr><td>ESMFold</td><td>esmfold</td><td style="color:#d29922">⚠️ openfold/omegaconf 의존성 누락</td><td>PyRosetta pose_from_sequence + FastRelax 로 대체</td></tr>
  <tr><td>Boltz-2</td><td>boltz</td><td style="color:#f85149">❌ MSA 서버 차단</td><td>api.colabfold.com 방화벽 차단 (sysadmin 요청 진행)</td></tr>
  <tr><td>HADDOCK</td><td>—</td><td style="color:#f85149">❌ 미설치</td><td>CNS 라이센스 필요, 추후 검토</td></tr>
</table>

<h2>SST-14 wild-type Ground Truth 비교</h2>
<div class="info">
  <strong>참고 데이터</strong>: SST-14의 SSTR1-5 결합 Ki (Patel YC, 1999; Hoyer et al., 1995).
  SSTR2가 최강 친화, SSTR4가 가장 약함. 모든 서브타입에 sub-nM ~ 수 nM Ki.
</div>
<table>
  <tr><th>수용체</th><th>SST-14 Ki (실측)</th><th>예상 결합 강도</th><th>측정 ddG</th><th>일치</th></tr>
  {"".join(gt_rows)}
</table>

<h2>10 후보 × 5 수용체 도킹 매트릭스</h2>
<table>
  <tr>
    <th>후보 ID</th><th>서열</th>
    <th>SSTR1</th><th>SSTR2</th><th>SSTR3</th><th>SSTR4</th><th>SSTR5</th>
    <th>Margin</th><th>Tier</th>
  </tr>
  {"".join(table_rows)}
</table>

<h2>방법론</h2>
<ul>
  <li><strong>수용체 전처리</strong>: 각 PDB의 HETATM/NCAA 제거 → canonical AA만 들어간 clean PDB 생성</li>
  <li><strong>Ground truth 위치</strong>: 원본 CIF의 NCAA 중심 좌표 추출 (SSTR1/2/3/4: HETATM 평균, SSTR5: chain A 펩타이드 ligand)</li>
  <li><strong>펩타이드 구조</strong>: PyRosetta <code>pose_from_sequence</code> + FastRelax (50 iter)</li>
  <li><strong>도킹 배치</strong>: 펩타이드 중심을 NCAA 중심에 정렬, jitter ±2 Å, nstruct=3</li>
  <li><strong>Minimize</strong>: MinMover (sidechain + jump, fixed backbone), dfpmin_armijo_nonmonotone, tol=0.5</li>
  <li><strong>Interface ddG</strong>: InterfaceAnalyzerMover, multi-jump 자동 탐색, max(dsasa) 가진 jump 채택</li>
  <li><strong>Tier 기준</strong>: T3 (margin ≤ -3.0), T2 (≤ -2.0), T1 (≤ -1.5), T0 (> -1.5)</li>
</ul>

<h2>알려진 한계 및 향후 작업</h2>
<div class="warning">
  <strong>본 보고서의 selectivity 값은 절대 친화도가 아닌 상대 순위 참고용입니다.</strong>
  PyRosetta fa_standard scoring function은 단백질-펩타이드 interface dG의 절대값 해석에 제한이 있으며,
  Boltz-2 / AlphaFold-Multimer 같은 deep learning 기반 다중 시퀀스 정합 모델과의 cross-validation이 필요합니다.
</div>
<ul>
  <li>네트워크 화이트리스트 후 Boltz-2 재실행 → 동일 50쌍 cross-validation</li>
  <li>SST-14 wild type의 SSTR1-5 실측 Ki와 본 결과의 Spearman 상관 측정</li>
  <li>HADDOCK 설치 후 trust-region 검증 (선택)</li>
  <li>각 후보의 ADMET 보정 → in-vivo 가용성 종합 평가</li>
</ul>

<div class="footer">
  Generated by <code>runs_local/selectivity_demo_20260511/generate_report.py</code> ·
  Data: <code>pyrosetta_batch/all_results.json</code> ·
  <a href="selectivity_demo.html" style="color:#58a6ff">이전 라운드 결과</a>
</div>

</body></html>"""
    return html


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch-dir", default="pyrosetta_batch")
    p.add_argument("--manifest", default="receptor_manifest.json")
    p.add_argument("--report-name", default="report.html")
    p.add_argument("--summary-name", default="selectivity_summary.json")
    args = p.parse_args()

    base_dir = Path("runs_local/selectivity_demo_20260511")
    pyrosetta_results, candidates, receptors = load_results(base_dir, args.batch_dir, args.manifest)
    per_cand = organize_by_candidate(pyrosetta_results)
    summary = compute_selectivity(per_cand)

    html = render_html(per_cand, summary, candidates, receptors)
    out_path = base_dir / args.report_name
    out_path.write_text(html)

    # JSON 요약도 같이 저장
    with open(base_dir / args.summary_name, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Report: {out_path}")
    print(f"Summary: {base_dir / args.summary_name}")
    print(f"Total candidates: {len(summary)}")
    for cid, s in summary.items():
        tier = s["tier"]
        margin = f"{s['margin']:.2f}" if s["margin"] is not None else "—"
        print(f"  {cid}: tier={tier}, margin={margin}")


if __name__ == "__main__":
    main()
