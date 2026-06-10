from __future__ import annotations

import argparse
import html
import json
import mimetypes
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from llm_benchmark.scoring.aggregate import OUTPUTS_DIR, load_phase_results

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / 'static'
PALETTE = ['#38bdf8', '#2dd4bf', '#f59e0b', '#fb7185', '#a78bfa', '#f97316', '#22c55e', '#eab308']


def esc(value: object) -> str:
    return html.escape(str(value))


def attr(value: object) -> str:
    return html.escape(str(value)).replace('"', '&quot;')


def safe_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def fmt_seconds(value: float | None) -> str:
    if value is None:
        return '-'
    if value < 60:
        return f'{value:.1f}s'
    minutes = int(value // 60)
    seconds = int(round(value % 60))
    return f'{minutes}m {seconds}s'


def fmt_signed_seconds(value: float | None) -> str:
    if value is None:
        return '-'
    sign = '+' if value >= 0 else '-'
    return sign + fmt_seconds(abs(value))


def fmt_num(value: float | None, digits: int = 3) -> str:
    if value is None:
        return '-'
    return f'{value:.{digits}f}'


def fmt_pct(value: float | None, digits: int = 0) -> str:
    if value is None:
        return '-'
    return f'{value * 100:.{digits}f}%'


def filter_attr_name(name: str) -> str:
    mapping = {'gate_mode': 'gate'}
    return mapping.get(name, name.replace('_', '-'))


def read_json(path: Path):
    if not path.exists() or not path.is_file() or path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None


def parse_run_name(run_name: str) -> dict[str, object]:
    parts = run_name.split('__')
    model = parts[0] if len(parts) >= 1 else 'unknown'
    flow = parts[1] if len(parts) >= 2 else 'sequential'
    gate_mode = 'static'
    seed = 0
    variant_parts = []  # phase2b rounds/orch, phase3 groups, etc.
    for part in parts[2:]:
        if part in ('static', 'adaptive'):
            gate_mode = part
        elif part.startswith('s') and part[1:].isdigit():
            seed = int(part[1:])
        else:
            variant_parts.append(part)
    variant = '__'.join(variant_parts) if variant_parts else ''
    return {'model': model, 'flow': flow, 'gate_mode': gate_mode, 'seed': seed, 'variant': variant}


def scan_raw_phase(phase: str) -> list[dict[str, object]]:
    phase_dir = OUTPUTS_DIR / phase
    if not phase_dir.exists():
        return []
    rows: list[dict[str, object]] = []
    for run_dir in sorted(p for p in phase_dir.iterdir() if p.is_dir() and not p.name.startswith('_')):
        status = read_json(run_dir / 'status.json') or {}
        config = read_json(run_dir / 'config_snapshot.json') or {}
        experiment = config.get('experiment', {}) if isinstance(config, dict) else {}
        parsed = parse_run_name(run_dir.name)
        rows.append(
            {
                'phase': phase,
                'run_name': run_dir.name,
                'model': experiment.get('model') or parsed['model'],
                'flow': experiment.get('flow') or parsed['flow'],
                'gate_mode': parsed['gate_mode'],
                'seed': experiment.get('seed', parsed['seed']),
                'state': status.get('state', 'unknown'),
                'elapsed_s': safe_float(status.get('elapsed_s')),
                'status_path': str((run_dir / 'status.json').relative_to(ROOT)),
            }
        )
    return rows


def scan_done_phase(phase: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in load_phase_results(phase):
        ses = result.get('ses', {}) if isinstance(result.get('ses'), dict) else {}
        run_dir = Path(str(result.get('run_dir', '')))
        rows.append(
            {
                'phase': phase,
                'run_name': run_dir.name,
                'model': str(result.get('model', 'unknown')),
                'flow': str(result.get('flow', 'sequential')),
                'gate_mode': str(result.get('gate_mode', 'static')),
                'seed': int(result.get('seed', 0) or 0),
                'elapsed_s': safe_float(result.get('elapsed_s')),
                'ses_score': safe_float(ses.get('ses')),
                'best_ddg': safe_float(ses.get('best_ddg')),
                'hit_rate': safe_float(ses.get('hit_rate')),
                'improvement': safe_float(ses.get('improvement')),
                'efficiency': safe_float(ses.get('efficiency')),
                'diversity': safe_float(ses.get('diversity')),
                'robustness': safe_float(ses.get('robustness')),
            }
        )
    return rows


def calc_span(values: list[float | None]) -> dict[str, float | None]:
    usable = [float(v) for v in values if v is not None]
    if not usable:
        return {'min': None, 'max': None}
    return {'min': min(usable), 'max': max(usable)}


def mark_frontier(rows: list[dict[str, object]]) -> set[str]:
    usable = [row for row in rows if row.get('elapsed_s') is not None and row.get('ses_score') is not None]
    frontier: set[str] = set()
    for row in usable:
        dominated = False
        for other in usable:
            if other is row:
                continue
            if float(other['elapsed_s']) <= float(row['elapsed_s']) and float(other['ses_score']) >= float(row['ses_score']) and (float(other['elapsed_s']) < float(row['elapsed_s']) or float(other['ses_score']) > float(row['ses_score'])):
                dominated = True
                break
        if not dominated:
            frontier.add(str(row['run_name']))
    return frontier


def build_envelope(rows: list[dict[str, object]], keys: tuple[str, ...], frontier_ids: set[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row[key]) for key in keys)].append(row)
    items: list[dict[str, object]] = []
    for group, group_rows in grouped.items():
        elapsed = [row.get('elapsed_s') for row in group_rows]
        ses = [row.get('ses_score') for row in group_rows if row.get('ses_score') is not None]
        ddg = [row.get('best_ddg') for row in group_rows if row.get('best_ddg') is not None]
        span = calc_span(elapsed)
        items.append(
            {
                'group': group,
                'runs': len(group_rows),
                'scored_runs': len(ses),
                'frontier_runs': sum(1 for row in group_rows if str(row['run_name']) in frontier_ids),
                'fastest_s': span['min'],
                'slowest_s': span['max'],
                'best_ses': max(ses) if ses else None,
                'best_ddg': min(ddg) if ddg else None,
            }
        )
    items.sort(key=lambda item: (item.get('best_ses') is None, -(item.get('best_ses') or -999), item.get('fastest_s') or 10**12))
    return items


def build_delta_pairs(rows: list[dict[str, object]], variant_key: str, base_keys: tuple[str, ...], metric_key: str) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row.get(metric_key) is None:
            continue
        grouped[tuple(str(row[key]) for key in base_keys)].append(row)
    pairs: list[dict[str, object]] = []
    for base, group_rows in grouped.items():
        by_variant = {str(row[variant_key]): row for row in group_rows}
        variants = sorted(by_variant)
        if len(variants) < 2:
            continue
        # Generate pairwise comparisons for all variant pairs (not just 2)
        for i in range(len(variants)):
            for j in range(i + 1, len(variants)):
                left_name, right_name = variants[i], variants[j]
                left = by_variant[left_name]
                right = by_variant[right_name]
                pairs.append(
                    {
                        'label': ' / '.join(base),
                        'seed': str(left.get('seed', '')),
                        'left_label': left_name,
                        'right_label': right_name,
                        'left_value': float(left[metric_key]),
                        'right_value': float(right[metric_key]),
                        'delta_value': float(right[metric_key]) - float(left[metric_key]),
                        'phase': str(left.get('phase', '')),
                        'model': str(left.get('model', '')),
                        'flow': '|'.join(sorted({str(row.get('flow', '')) for row in [left, right]})),
                        'gate': '|'.join(sorted({str(row.get('gate_mode', '')) for row in [left, right]})),
                    }
                )
    pairs.sort(key=lambda item: (abs(item['delta_value']), item['label']), reverse=True)
    return pairs


def build_heatmap(raw_rows: list[dict[str, object]]) -> tuple[list[int], list[dict[str, object]]]:
    seeds = sorted({int(row['seed']) for row in raw_rows})
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in raw_rows:
        variant = row.get('variant', '')
        variant_suffix = f" [{variant}]" if variant else ''
        grouped[f"{row['model']} / {row['gate_mode']}{variant_suffix}"].append(row)
    result: list[dict[str, object]] = []
    for label, group_rows in sorted(grouped.items()):
        # Use (seed, variant) as key to avoid overwrite when same seed has multiple variants
        by_seed: dict[int, dict[str, object]] = {}
        for row in group_rows:
            s = int(row['seed'])
            if s not in by_seed:
                by_seed[s] = row
        sample = group_rows[0]
        result.append(
            {
                'label': label,
                'model': str(sample['model']),
                'flow': str(sample['flow']),
                'gate_mode': str(sample['gate_mode']),
                'cells': [
                    {
                        'seed': seed,
                        'elapsed_s': by_seed.get(seed, {}).get('elapsed_s'),
                        'state': by_seed.get(seed, {}).get('state', 'missing'),
                    }
                    for seed in seeds
                ],
            }
        )
    return seeds, result


def collect_data() -> dict[str, object]:
    phases: list[dict[str, object]] = []
    all_done: list[dict[str, object]] = []
    all_raw: list[dict[str, object]] = []
    if not OUTPUTS_DIR.exists():
        return {'outputs_root': str(OUTPUTS_DIR.relative_to(ROOT)), 'available_phases': [], 'phases': [], 'summary': {}}
    for phase_dir in sorted(p for p in OUTPUTS_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')):
        phase = phase_dir.name
        raw_rows = scan_raw_phase(phase)
        done_rows = scan_done_phase(phase)
        scored_rows = [row for row in done_rows if row.get('ses_score') is not None]
        frontier_ids = mark_frontier(done_rows)
        seeds, heatmap_rows = build_heatmap(raw_rows)
        phases.append(
            {
                'phase': phase,
                'raw_rows': raw_rows,
                'done_rows': done_rows,
                'scored_rows': scored_rows,
                'frontier_ids': frontier_ids,
                'runtime_span': calc_span([row.get('elapsed_s') for row in done_rows]),
                'state_counts': dict(Counter(str(row['state']) for row in raw_rows)),
                'models': sorted({str(row['model']) for row in raw_rows} | {str(row['model']) for row in done_rows}),
                'flows': sorted({str(row['flow']) for row in raw_rows} | {str(row['flow']) for row in done_rows}),
                'gates': sorted({str(row['gate_mode']) for row in raw_rows} | {str(row['gate_mode']) for row in done_rows}),
                'heatmap_seeds': seeds,
                'heatmap_rows': heatmap_rows,
                'model_env': build_envelope(done_rows, ('model',), frontier_ids),
                'flow_env': build_envelope(done_rows, ('model', 'flow'), frontier_ids),
                'gate_env': build_envelope(done_rows, ('gate_mode',), frontier_ids),
            }
        )
        all_done.extend(done_rows)
        all_raw.extend(raw_rows)
    all_frontier_ids = mark_frontier(all_done)
    all_scored_rows = [row for row in all_done if row.get('ses_score') is not None]
    return {
        'outputs_root': str(OUTPUTS_DIR.relative_to(ROOT)),
        'available_phases': [phase['phase'] for phase in phases],
        'phases': phases,
        'summary': {
            'phase_count': len(phases),
            'total_completed_runs': len(all_done),
            'total_scored_runs': len(all_scored_rows),
            'all_scored_rows': all_scored_rows,
            'all_done_rows': all_done,
            'all_raw_rows': all_raw,
            'all_frontier_ids': all_frontier_ids,
            'all_models': sorted({str(row['model']) for row in all_done}),
            'all_flows': sorted({str(row['flow']) for row in all_done}),
            'all_gates': sorted({str(row['gate_mode']) for row in all_done}),
            'model_env': build_envelope(all_done, ('model',), all_frontier_ids),
            'flow_env': build_envelope(all_done, ('flow',), all_frontier_ids),
            'gate_env': build_envelope(all_done, ('gate_mode',), all_frontier_ids),
        },
    }


def render_filter_panel(filter_id: str, options: dict[str, list[str]]) -> str:
    groups = []
    for key, values in options.items():
        if not values:
            continue
        chips = ''.join(
            f"<label class='filter-chip'><input type='checkbox' data-filter-key='{key}' value='{attr(value)}' checked /> <span>{esc(value)}</span></label>"
            for value in values
        )
        groups.append(f"<div class='filter-group'><div class='filter-label'>{esc(key)}</div><div class='filter-values'>{chips}</div></div>")
    if not groups:
        return ''
    return f"<section class='panel filters' data-filter-root='{filter_id}'><div class='filter-top'><h3>Filters</h3><button type='button' class='filter-reset'>Reset</button></div><div class='filter-active small-note'>All values active</div>{''.join(groups)}</section>"


def render_table(headers: list[str], rows: list[str]) -> str:
    head = ''.join(f'<th>{esc(header)}</th>' for header in headers)
    body = ''.join(rows) if rows else "<tr><td colspan='99' class='empty'>No rows</td></tr>"
    return f"<div class='table-wrap'><table class='table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def wrap_row(cells: list[str], attrs_dict: dict[str, object] | None = None) -> str:
    attrs_html = ''
    if attrs_dict:
        attrs_html = ' ' + ' '.join(f"data-{key}='{attr(value)}'" for key, value in attrs_dict.items())
    row_class = " class='interactive-node'" if attrs_dict else ""
    return f"<tr{row_class}{attrs_html}>" + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'




def render_legend(labels: list[str], legend_key: str) -> tuple[str, dict[str, str]]:
    colors = {label: PALETTE[i % len(PALETTE)] for i, label in enumerate(labels)}
    html_items = ''.join(
        f"<button type='button' class='legend-item' data-legend-key='{attr(legend_key)}' data-legend-value='{attr(label)}'><span class='legend-dot' style='background:{color}'></span>{esc(label)}</button>"
        for label, color in colors.items()
    )
    return html_items, colors


def render_scatter(rows: list[dict[str, object]], x_key: str, y_key: str, color_key: str, x_label: str, y_label: str, filter_id: str, maximize_y: bool = True) -> str:
    usable = [row for row in rows if row.get(x_key) is not None and row.get(y_key) is not None]
    if not usable:
        return "<div class='empty'>Trade-off plot unavailable.</div>"
    width, height = 920, 420
    left, right, top, bottom = 72, 24, 22, 58
    xs = [float(row[x_key]) for row in usable]
    ys = [float(row[y_key]) for row in usable]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0
    labels = []
    for row in usable:
        label = str(row[color_key])
        if label not in labels:
            labels.append(label)
    legend_html, colors = render_legend(labels, 'gate' if color_key == 'gate_mode' else color_key)
    frontier = mark_frontier(rows) if y_key == 'ses_score' else set()
    circles = []
    for row in usable:
        cx = left + ((float(row[x_key]) - x_min) / (x_max - x_min)) * (width - left - right)
        ratio = (float(row[y_key]) - y_min) / (y_max - y_min)
        cy = top + ((1.0 - ratio) if maximize_y else ratio) * (height - top - bottom)
        color = colors[str(row[color_key])]
        active = str(row['run_name']) in frontier
        _r = '6.5' if active else '5.0'
        _stroke = '#ffffff' if active else color
        _sw = '2.6' if active else '1.0'
        _tip = f"{row['phase']} | {row['model']} | {row['flow']} | {row['gate_mode']} | seed {row['seed']}"
        circles.append(
            f"<circle class='plot-point interactive-node' data-filter-target='{filter_id}' data-filter-mode='all' data-phase='{attr(row['phase'])}' data-model='{attr(row['model'])}' data-flow='{attr(row['flow'])}' data-gate='{attr(row['gate_mode'])}' data-tip='{attr(_tip)}' cx='{cx:.1f}' cy='{cy:.1f}' r='{_r}' fill='{color}' fill-opacity='0.88' stroke='{_stroke}' stroke-width='{_sw}'><title>{esc(_tip)}</title></circle>"
        )
    return f"<div class='viz-shell'><svg class='chart-svg' viewBox='0 0 {width} {height}'><line x1='{left}' y1='{top}' x2='{left}' y2='{height-bottom}' class='axis-line' /><line x1='{left}' y1='{height-bottom}' x2='{width-right}' y2='{height-bottom}' class='axis-line' /><text x='{left}' y='{top-4}' class='axis-text'>{esc(y_label)} {(fmt_num(y_max, 4) if maximize_y else fmt_num(y_min, 3))}</text><text x='{left}' y='{height-bottom+24}' class='axis-text'>{esc(x_label)} {esc(fmt_seconds(x_min))}</text><text x='{width-right}' y='{height-bottom+24}' text-anchor='end' class='axis-text'>{esc(fmt_seconds(x_max))}</text><text x='{width/2}' y='{height-12}' text-anchor='middle' class='axis-label'>{esc(x_label)}</text><text x='22' y='{height/2}' transform='rotate(-90 22 {height/2})' text-anchor='middle' class='axis-label'>{esc(y_label)}</text>{''.join(circles)}</svg><div class='legend'>{legend_html}</div></div>"


def render_delta_chart(pairs: list[dict[str, object]], filter_id: str, value_formatter=None, value_suffix: str = 'delta') -> str:
    if not pairs:
        return "<div class='empty'>Comparable paired runs are not available for this view.</div>"
    values = [pair['left_value'] for pair in pairs] + [pair['right_value'] for pair in pairs]
    lo, hi = min(values), max(values)
    if lo == hi:
        lo -= 1.0
        hi += 1.0
    if value_formatter is None:
        value_formatter = fmt_signed_seconds
    point_formatter = fmt_seconds if value_suffix == 'runtime delta' else (lambda value: fmt_num(value, 4))
    parts = []
    for pair in pairs:
        left_pct = ((pair['left_value'] - lo) / (hi - lo)) * 100.0
        right_pct = ((pair['right_value'] - lo) / (hi - lo)) * 100.0
        line_left = min(left_pct, right_pct)
        line_width = max(abs(right_pct - left_pct), 1.2)
        _dtip = f"{pair['label']} | seed {pair['seed']} | {pair['left_label']} -> {pair['right_label']}"
        parts.append(
            f"<div class='delta-row interactive-node' data-filter-target='{filter_id}' data-filter-mode='all' data-phase='{attr(pair['phase'])}' data-model='{attr(pair['model'])}' data-flow='{attr(pair['flow'])}' data-gate='{attr(pair['gate'])}' data-tip='{attr(_dtip)}'><div class='delta-meta'><div class='delta-title'>{esc(pair['label'])}</div><div class='delta-caption'>seed {esc(pair['seed'])} | {esc(pair['left_label'])} {esc(point_formatter(pair['left_value']))} -> {esc(pair['right_label'])} {esc(point_formatter(pair['right_value']))}</div></div><div class='delta-track'><div class='delta-line' style='left:{line_left:.2f}%; width:{line_width:.2f}%'></div><div class='delta-dot left' style='left:{left_pct:.2f}%'></div><div class='delta-dot right' style='left:{right_pct:.2f}%'></div></div><div class='delta-value'>{esc(value_formatter(pair['delta_value']))}<span>{esc(value_suffix)}</span></div></div>"
        )
    return f"<div class='delta-chart'>{''.join(parts)}</div>"


def render_seed_strip(rows: list[dict[str, object]], metric_key: str, metric_label: str, filter_id: str, color_key: str = 'gate_mode') -> str:
    usable = [row for row in rows if row.get(metric_key) is not None]
    if not usable:
        return "<div class='empty'>Seed-level strip plot unavailable.</div>"
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in usable:
        grouped[str(row['model'])].append(row)
    values = [float(row[metric_key]) for row in usable]
    lo, hi = min(values), max(values)
    if lo == hi:
        lo -= 1.0
        hi += 1.0
    width, row_h = 920, 58
    left, right, top, bottom = 168, 24, 24, 42
    height = top + bottom + row_h * len(grouped)
    labels = []
    for row in usable:
        label = str(row[color_key])
        if label not in labels:
            labels.append(label)
    legend_html, colors = render_legend(labels, 'gate' if color_key == 'gate_mode' else color_key)
    parts = [f"<line x1='{left}' y1='{height-bottom}' x2='{width-right}' y2='{height-bottom}' class='axis-line' />"]
    for idx, model in enumerate(sorted(grouped)):
        y = top + idx * row_h + row_h / 2
        parts.append(f"<text x='{left-14}' y='{y+4:.1f}' text-anchor='end' class='axis-text'>{esc(model)}</text>")
        parts.append(f"<line x1='{left}' y1='{y:.1f}' x2='{width-right}' y2='{y:.1f}' class='axis-line' style='stroke-opacity:0.35' />")
        for row in grouped[model]:
            ratio = (float(row[metric_key]) - lo) / (hi - lo)
            cx = left + ratio * (width - left - right)
            label = str(row[color_key])
            color = colors[label]
            _stip = f"{row['phase']} | {row['model']} | {row['flow']} | {row['gate_mode']} | seed {row['seed']}"
            parts.append(
                f"<circle class='plot-point interactive-node' data-filter-target='{filter_id}' data-filter-mode='all' data-phase='{attr(row['phase'])}' data-model='{attr(row['model'])}' data-flow='{attr(row['flow'])}' data-gate='{attr(row['gate_mode'])}' data-tip='{attr(_stip)}' cx='{cx:.1f}' cy='{y:.1f}' r='7' fill='{color}' fill-opacity='0.9' stroke='{color}' stroke-width='1.2'><title>{esc(row['phase'])} | {esc(row['model'])} | {esc(row['flow'])} | {esc(row['gate_mode'])} | seed {row['seed']} | {esc(metric_label)} {esc(fmt_seconds(row[metric_key]) if metric_key == 'elapsed_s' else fmt_num(row[metric_key], 4))}</title></circle>"
            )
            parts.append(f"<text x='{cx:.1f}' y='{y-12:.1f}' text-anchor='middle' class='axis-text'>{esc(row['seed'])}</text>")
    lo_label = fmt_seconds(lo) if metric_key == 'elapsed_s' else fmt_num(lo, 4)
    hi_label = fmt_seconds(hi) if metric_key == 'elapsed_s' else fmt_num(hi, 4)
    return f"<div class='viz-shell'><svg class='chart-svg' viewBox='0 0 {width} {height}'><text x='{left}' y='{height-bottom+24}' class='axis-text'>{esc(metric_label)} {esc(lo_label)}</text><text x='{width-right}' y='{height-bottom+24}' text-anchor='end' class='axis-text'>{esc(hi_label)}</text><text x='{width/2}' y='{height-10}' text-anchor='middle' class='axis-label'>{esc(metric_label)}</text>{''.join(parts)}</svg><div class='legend'>{legend_html}</div></div>"


def render_coverage_matrix(raw_rows: list[dict[str, object]], label_keys: tuple[str, ...], filter_id: str) -> str:
    if not raw_rows:
        return "<div class='empty'>Coverage matrix unavailable.</div>"
    seeds = sorted({int(row['seed']) for row in raw_rows})
    grouped: dict[tuple[str, ...], dict[int, dict[str, object]]] = defaultdict(dict)
    for row in raw_rows:
        key = tuple(str(row[k]) for k in label_keys)
        grouped[key][int(row['seed'])] = row
    state_colors = {
        'done': 'rgba(45, 212, 191, 0.26)',
        'running': 'rgba(56, 189, 248, 0.24)',
        'failed': 'rgba(251, 113, 133, 0.24)',
        'missing': 'var(--heat-empty)',
    }
    head = ''.join(f"<div class='heat-label heat-head'>seed {seed}</div>" for seed in seeds)
    rows_html = []
    template = f"260px repeat({len(seeds)}, minmax(112px, 1fr))"
    for key in sorted(grouped):
        seed_map = grouped[key]
        attrs = ' '.join(f"data-{filter_attr_name(k)}='{attr(v)}'" for k, v in zip(label_keys, key))
        cells = []
        for seed in seeds:
            row = seed_map.get(seed)
            state = str(row['state']) if row else 'missing'
            bg = state_colors.get(state, 'rgba(245, 158, 11, 0.22)')
            caption = fmt_seconds(row.get('elapsed_s')) if row and row.get('elapsed_s') is not None else '-'
            cells.append(f"<div class='heat-cell' style='background:{bg}'><strong>{esc(state)}</strong><span class='small-note'>{esc(caption)}</span></div>")
        rows_html.append(f"<div class='heatmap-row interactive-node' data-filter-target='{filter_id}' {attrs} data-tip='{attr(' / '.join(key))}' style='grid-template-columns:{template};'><div class='heat-label'>{esc(' / '.join(key))}</div>{''.join(cells)}</div>")
    return f"<div class='heatmap'><div class='heatmap-row' style='grid-template-columns:{template};'><div></div>{head}</div>{''.join(rows_html)}</div>"


def render_component_strip(rows: list[dict[str, object]], metric_keys: tuple[str, ...], filter_id: str) -> str:
    usable = [row for row in rows if any(row.get(key) is not None for key in metric_keys)]
    if not usable:
        return "<div class='empty'>SES component breakdown unavailable.</div>"
    labels = list(metric_keys)
    width, height = 920, max(260, 72 + len(labels) * 64)
    left, right, top, bottom = 172, 24, 26, 40
    legend_html, colors = render_legend(labels, 'component')
    parts = [f"<line x1='{left}' y1='{height-bottom}' x2='{width-right}' y2='{height-bottom}' class='axis-line' />"]
    for idx, key in enumerate(labels):
        y = top + idx * 56 + 24
        parts.append(f"<text x='{left-14}' y='{y+4:.1f}' text-anchor='end' class='axis-text'>{esc(key)}</text>")
        parts.append(f"<line x1='{left}' y1='{y:.1f}' x2='{width-right}' y2='{y:.1f}' class='axis-line' style='stroke-opacity:0.35' />")
        values = [float(row[key]) for row in usable if row.get(key) is not None]
        lo, hi = (min(values), max(values)) if values else (0.0, 1.0)
        if lo == hi:
            lo -= 0.1
            hi += 0.1
        for row in usable:
            if row.get(key) is None:
                continue
            ratio = (float(row[key]) - lo) / (hi - lo)
            cx = left + ratio * (width - left - right)
            _ctip = f"{row['phase']} | {row['model']} | {row['flow']} | {row['gate_mode']} | seed {row['seed']}"
            parts.append(
                f"<circle class='plot-point interactive-node' data-filter-target='{filter_id}' data-filter-mode='all' data-phase='{attr(row['phase'])}' data-model='{attr(row['model'])}' data-flow='{attr(row['flow'])}' data-gate='{attr(row['gate_mode'])}' data-component='{attr(key)}' data-tip='{attr(_ctip)}' cx='{cx:.1f}' cy='{y:.1f}' r='6.2' fill='{colors[key]}' fill-opacity='0.88' stroke='{colors[key]}' stroke-width='1.0'><title>{esc(row['phase'])} | {esc(row['model'])} | {esc(row['flow'])} | {esc(row['gate_mode'])} | seed {row['seed']} | {esc(key)} {esc(fmt_num(row[key], 4))}</title></circle>"
            )
    return f"<div class='viz-shell'><svg class='chart-svg' viewBox='0 0 {width} {height}'><text x='{left}' y='{height-bottom+24}' class='axis-text'>lower</text><text x='{width-right}' y='{height-bottom+24}' text-anchor='end' class='axis-text'>higher</text><text x='{width/2}' y='{height-10}' text-anchor='middle' class='axis-label'>SES components</text>{''.join(parts)}</svg><div class='legend'>{legend_html}</div></div>"


def render_frontier_contrib(rows: list[dict[str, object]], frontier_ids: set[str], group_keys: tuple[str, ...], filter_id: str) -> str:
    grouped: dict[tuple[str, ...], dict[str, int]] = defaultdict(lambda: {'frontier': 0, 'scored': 0})
    for row in rows:
        key = tuple(str(row[k]) for k in group_keys)
        grouped[key]['scored'] += 1
        if str(row['run_name']) in frontier_ids:
            grouped[key]['frontier'] += 1
    table_rows = []
    items = sorted(grouped.items(), key=lambda item: (-item[1]['frontier'], -item[1]['scored'], item[0]))
    for key, counts in items:
        attrs = {'filter-target': filter_id}
        for name, value in zip(group_keys, key):
            attrs[filter_attr_name(name)] = value
        ratio = counts['frontier'] / counts['scored'] if counts['scored'] else 0.0
        table_rows.append(wrap_row([esc(' / '.join(key)), f"<span class='mono'>{counts['frontier']}</span>", f"<span class='mono'>{counts['scored']}</span>", f"<span class='mono'>{ratio:.2f}</span>"], attrs))
    headers = ['Group', 'Frontier', 'Scored', 'Frontier Ratio']
    return render_table(headers, table_rows)


def render_ddg_frontier(rows: list[dict[str, object]], filter_id: str) -> str:
    usable = [row for row in rows if row.get('elapsed_s') is not None and row.get('best_ddg') is not None]
    if not usable:
        return "<div class='empty'>ddG frontier unavailable.</div>"
    frontier = set()
    for row in usable:
        dominated = False
        for other in usable:
            if other is row:
                continue
            if float(other['elapsed_s']) <= float(row['elapsed_s']) and float(other['best_ddg']) <= float(row['best_ddg']) and (float(other['elapsed_s']) < float(row['elapsed_s']) or float(other['best_ddg']) < float(row['best_ddg'])):
                dominated = True
                break
        if not dominated:
            frontier.add(str(row['run_name']))
    rows_html = []
    for row in sorted([r for r in usable if str(r['run_name']) in frontier], key=lambda r: (r['elapsed_s'], r['best_ddg'])):
        rows_html.append(wrap_row([esc(row['phase']), esc(row['model']), esc(row['flow']), esc(row['gate_mode']), f"<span class='mono'>{row['seed']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['elapsed_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ddg'], 3))}</span>"], {'filter-target': filter_id, 'phase': row['phase'], 'model': row['model'], 'flow': row['flow'], 'gate': row['gate_mode']}))
    return render_table(['Phase', 'Model', 'Flow', 'Gate', 'Seed', 'Runtime', 'best ddG'], rows_html)


def render_insight_cards(items: list[dict[str, object]]) -> str:
    cards = []
    for item in items:
        tone = str(item.get('tone', '')).strip()
        class_name = 'insight-card' + (f' {tone}' if tone else '')
        cards.append(
            f"<article class='{attr(class_name)}'><div class='insight-label'>{esc(item.get('label', 'Insight'))}</div><div class='insight-value'>{item.get('value_html', esc(item.get('value', '-')))}</div><p>{esc(item.get('caption', ''))}</p></article>"
        )
    return f"<div class='insight-grid'>{''.join(cards)}</div>"


def build_overview_insights(data: dict[str, object]) -> list[dict[str, object]]:
    phases = data['phases']
    summary = data['summary']
    items: list[dict[str, object]] = []
    if phases:
        best_coverage = max(phases, key=lambda phase: ((len(phase['scored_rows']) / len(phase['done_rows'])) if phase['done_rows'] else 0.0, len(phase['scored_rows'])))
        coverage_ratio = (len(best_coverage['scored_rows']) / len(best_coverage['done_rows'])) if best_coverage['done_rows'] else 0.0
        items.append({'label': 'Best Score Coverage', 'value': best_coverage['phase'], 'caption': f"{len(best_coverage['scored_rows'])}/{len(best_coverage['done_rows'])} completed runs are scored ({fmt_pct(coverage_ratio)}).", 'tone': 'tone-accent'})
        widest_phase = max(phases, key=lambda phase: ((phase['runtime_span']['max'] or 0) - (phase['runtime_span']['min'] or 0), len(phase['done_rows'])))
        widest_span = ((widest_phase['runtime_span']['max'] or 0) - (widest_phase['runtime_span']['min'] or 0)) if widest_phase['runtime_span']['max'] is not None and widest_phase['runtime_span']['min'] is not None else None
        items.append({'label': 'Widest Runtime Surface', 'value': widest_phase['phase'], 'caption': f"Runtime stretches by {fmt_seconds(widest_span)} inside this phase, so seed/model effects are easiest to spot there.", 'tone': 'tone-warn'})
    if summary['all_done_rows']:
        fastest = min((row for row in summary['all_done_rows'] if row.get('elapsed_s') is not None), key=lambda row: float(row['elapsed_s']))
        items.append({'label': 'Fastest Completed Run', 'value_html': f"{esc(fastest['model'])} <span class='mono'>{esc(fmt_seconds(fastest['elapsed_s']))}</span>", 'caption': f"{fastest['phase']} / {fastest['flow']} / {fastest['gate_mode']} / seed {fastest['seed']}", 'tone': 'tone-cool'})
    if summary['all_scored_rows']:
        best_ses = max((row for row in summary['all_scored_rows'] if row.get('ses_score') is not None), key=lambda row: float(row['ses_score']))
        frontier_counter = Counter(row['model'] for row in summary['all_scored_rows'] if str(row['run_name']) in summary['all_frontier_ids'])
        dominant_model, dominant_count = frontier_counter.most_common(1)[0] if frontier_counter else ('-', 0)
        items.append({'label': 'Best SES Run', 'value_html': f"<span class='mono'>{esc(fmt_num(best_ses['ses_score'], 4))}</span>", 'caption': f"{best_ses['phase']} / {best_ses['model']} / {best_ses['gate_mode']} / seed {best_ses['seed']}", 'tone': 'tone-good'})
        items.append({'label': 'Frontier Pressure', 'value': str(dominant_model), 'caption': f"{dominant_count} of {len(summary['all_frontier_ids'])} SES frontier runs belong to this model.", 'tone': 'tone-hot'})
    return items


def build_phase_insights(phase: dict[str, object], gate_pairs: list[dict[str, object]], flow_pairs: list[dict[str, object]]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    coverage = (len(phase['scored_rows']) / len(phase['done_rows'])) if phase['done_rows'] else 0.0
    items.append({'label': 'Score Coverage', 'value': fmt_pct(coverage), 'caption': f"{len(phase['scored_rows'])} of {len(phase['done_rows'])} completed runs can participate in score-side trade-off analysis.", 'tone': 'tone-accent' if coverage >= 0.75 else 'tone-warn'})
    if phase['done_rows']:
        fastest = min((row for row in phase['done_rows'] if row.get('elapsed_s') is not None), key=lambda row: float(row['elapsed_s']))
        items.append({'label': 'Fastest Completed Run', 'value_html': f"{esc(fastest['model'])} <span class='mono'>{esc(fmt_seconds(fastest['elapsed_s']))}</span>", 'caption': f"{fastest['flow']} / {fastest['gate_mode']} / seed {fastest['seed']}", 'tone': 'tone-cool'})
    if phase['scored_rows']:
        best_ses = max((row for row in phase['scored_rows'] if row.get('ses_score') is not None), key=lambda row: float(row['ses_score']))
        items.append({'label': 'Best SES Run', 'value_html': f"<span class='mono'>{esc(fmt_num(best_ses['ses_score'], 4))}</span>", 'caption': f"{best_ses['model']} / {best_ses['flow']} / {best_ses['gate_mode']} / seed {best_ses['seed']}", 'tone': 'tone-good'})
    if gate_pairs:
        strongest_gate = max(gate_pairs, key=lambda pair: abs(float(pair['delta_value'])))
        direction = f"{strongest_gate['left_label']} -> {strongest_gate['right_label']}"
        items.append({'label': 'Strongest Gate Shift', 'value_html': f"<span class='mono'>{esc(fmt_signed_seconds(strongest_gate['delta_value']))}</span>", 'caption': f"{strongest_gate['label']} | {direction} produces the largest runtime delta.", 'tone': 'tone-hot'})
    if flow_pairs:
        strongest_flow = max(flow_pairs, key=lambda pair: abs(float(pair['delta_value'])))
        direction = f"{strongest_flow['left_label']} -> {strongest_flow['right_label']}"
        items.append({'label': 'Strongest Flow Shift', 'value_html': f"<span class='mono'>{esc(fmt_signed_seconds(strongest_flow['delta_value']))}</span>", 'caption': f"{strongest_flow['label']} | {direction} is the biggest flow-side runtime change.", 'tone': 'tone-warn'})
    return items


def render_reading_guide(items: list[str]) -> str:
    return "<div class='reading-guide'>" + ''.join(f"<div class='reading-item'>{esc(item)}</div>" for item in items) + "</div>"


def phase_url(phase: str) -> str:
    return '/?' + urlencode({'view': 'phase', 'phase': phase})


def overview_url() -> str:
    return '/?' + urlencode({'view': 'overview'})


def render_nav(data: dict[str, object], current_view: str, current_phase: str | None) -> str:
    overview_class = 'active' if current_view == 'overview' else ''
    links = [f"<a class='nav-link {overview_class}' href='{overview_url()}'>Overview</a>"]
    for phase in data['available_phases']:
        active = 'active' if current_view == 'phase' and current_phase == phase else ''
        links.append(f"<a class='nav-link {active}' href='{phase_url(str(phase))}'>{esc(phase)}</a>")
    return f"<nav class='top-nav'><div class='nav-group'>{''.join(links)}</div><div class='nav-group'><button id='compact-toggle' class='theme-toggle' type='button'>Compact</button><button id='export-snapshot' class='theme-toggle' type='button'>Export</button><button id='theme-toggle' class='theme-toggle' type='button'>Theme</button></div></nav>"


def render_overview(data: dict[str, object]) -> str:
    summary = data['summary']
    filter_id = 'overview'
    filters = render_filter_panel(filter_id, {'phase': data['available_phases'], 'model': summary['all_models'], 'flow': summary['all_flows'], 'gate': summary['all_gates']})
    insight_cards = render_insight_cards(build_overview_insights(data))
    guide = render_reading_guide([
        'Use Runtime vs SES to find the trade-off surface; frontier rows are the non-dominated candidates.',
        'Use Coverage Matrix before comparing flows or gates; sparse cells mean the comparison is structurally weak.',
        'Use envelope and frontier tables to see who repeatedly shows up near the boundary, not who wins on average.',
    ])
    phase_rows: list[str] = []
    for phase in data['phases']:
        phase_rows.append(
            wrap_row(
                [
                    f"<a href='{phase_url(str(phase['phase']))}' class='table-link'>{esc(phase['phase'])}</a>",
                    f"<span class='mono'>{len(phase['raw_rows'])}</span>",
                    f"<span class='mono'>{len(phase['done_rows'])}</span>",
                    f"<span class='mono'>{len(phase['scored_rows'])}</span>",
                    esc(', '.join(phase['models']) or '-'),
                    esc(', '.join(phase['flows']) or '-'),
                    esc(', '.join(phase['gates']) or '-'),
                ]
            )
        )
    frontier_rows: list[str] = []
    frontier_sorted = sorted(
        [row for row in summary['all_scored_rows'] if str(row['run_name']) in summary['all_frontier_ids']],
        key=lambda row: (row.get('elapsed_s') or 10**12, -(row.get('ses_score') or 0)),
    )
    for row in frontier_sorted:
        frontier_rows.append(
            wrap_row(
                [
                    esc(row['phase']),
                    esc(row['model']),
                    esc(row['flow']),
                    esc(row['gate_mode']),
                    f"<span class='mono'>{row['seed']}</span>",
                    f"<span class='mono'>{esc(fmt_seconds(row['elapsed_s']))}</span>",
                    f"<span class='mono'>{esc(fmt_num(row['ses_score'], 4))}</span>",
                    f"<span class='mono'>{esc(fmt_num(row['best_ddg'], 3))}</span>",
                ],
                {'filter-target': filter_id, 'phase': row['phase'], 'model': row['model'], 'flow': row['flow'], 'gate': row['gate_mode']},
            )
        )
    model_rows = [wrap_row([esc(row['group'][0]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ddg'], 3))}</span>"], {'filter-target': filter_id, 'model': row['group'][0]}) for row in summary['model_env']]
    flow_rows = [wrap_row([esc(row['group'][0]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>"], {'filter-target': filter_id, 'flow': row['group'][0]}) for row in summary['flow_env']]
    gate_rows = [wrap_row([esc(row['group'][0]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>"], {'filter-target': filter_id, 'gate': row['group'][0]}) for row in summary['gate_env']]
    return f"<section class='hero'><div class='hero-top'><div><span class='badge'>LLM Benchmark Observatory</span><h1>All-Phase Trade-off Overview</h1><p><span class='mono'>{esc(data['outputs_root'])}</span> compares each run directly without averages.</p></div></div><section class='kpis'><article class='kpi'><div class='eyebrow'>Phases</div><div class='value'>{summary['phase_count']}</div></article><article class='kpi'><div class='eyebrow'>Completed Runs</div><div class='value'>{summary['total_completed_runs']}</div></article><article class='kpi'><div class='eyebrow'>Scored Runs</div><div class='value'>{summary['total_scored_runs']}</div></article><article class='kpi'><div class='eyebrow'>Frontier Runs</div><div class='value'>{len(summary['all_frontier_ids'])}</div></article></section></section>{filters}<section class='grid-2'><section class='panel panel-hero-copy'><h3>Quick Read</h3><p class='sub'>high-signal statements extracted from the current run set</p>{insight_cards}</section><section class='panel'><h3>How To Read This Page</h3><p class='sub'>use these panels in this order when comparing LLMs or flows</p>{guide}</section></section><section class='grid-2'><section class='panel'><h3>Phase Coverage</h3><p class='sub'>phase directories and scored coverage</p>{render_table(['Phase','Run Dirs','Completed','Scored','Models','Flows','Gates'], phase_rows)}</section><section class='panel'><h3>Cross-Phase Runtime vs SES</h3><p class='sub'>each dot is one scored run</p>{render_scatter(summary['all_scored_rows'], 'elapsed_s', 'ses_score', 'phase', 'Runtime', 'SES', filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Cross-Phase Runtime vs best ddG</h3><p class='sub'>lower ddG is better</p>{render_scatter(summary['all_scored_rows'], 'elapsed_s', 'best_ddg', 'model', 'Runtime', 'best ddG', filter_id, maximize_y=False)}</section><section class='panel'><h3>Pareto Frontier Ledger</h3>{render_table(['Phase','Model','Flow','Gate','Seed','Runtime','SES','best ddG'], frontier_rows)}</section></section><section class='grid-2'><section class='panel'><h3>ddG Frontier Ledger</h3><p class='sub'>runtime x best ddG non-dominated runs</p>{render_ddg_frontier(summary['all_scored_rows'], filter_id)}</section><section class='panel'><h3>Cross-Phase Coverage Matrix</h3><p class='sub'>phase / model / flow / gate by seed coverage</p>{render_coverage_matrix(summary['all_raw_rows'], ('phase', 'model', 'flow', 'gate_mode'), filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Cross-Phase Runtime Strip</h3><p class='sub'>run-level runtime spread by model, colored by phase</p>{render_seed_strip(summary['all_done_rows'], 'elapsed_s', 'Runtime', filter_id, color_key='phase')}</section><section class='panel'><h3>Runtime vs Hit Rate</h3><p class='sub'>run-level yield vs runtime</p>{render_scatter(summary['all_scored_rows'], 'elapsed_s', 'hit_rate', 'model', 'Runtime', 'Hit Rate', filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Runtime vs Improvement</h3><p class='sub'>run-level improvement vs runtime</p>{render_scatter(summary['all_scored_rows'], 'elapsed_s', 'improvement', 'gate_mode', 'Runtime', 'Improvement', filter_id)}</section><section class='panel'><h3>Frontier by Model</h3>{render_frontier_contrib(summary['all_scored_rows'], summary['all_frontier_ids'], ('model',), filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Frontier by Flow</h3>{render_frontier_contrib(summary['all_scored_rows'], summary['all_frontier_ids'], ('flow',), filter_id)}</section><section class='panel'><h3>Frontier by Gate</h3>{render_frontier_contrib(summary['all_scored_rows'], summary['all_frontier_ids'], ('gate_mode',), filter_id)}</section></section><section class='grid-3'><section class='panel'><h3>LLM Envelope</h3>{render_table(['Model','Runs','Scored','Frontier','Fastest','Slowest','Best SES','Best ddG'], model_rows)}</section><section class='panel'><h3>Flow Envelope</h3>{render_table(['Flow','Runs','Scored','Frontier','Fastest','Slowest','Best SES'], flow_rows)}</section><section class='panel'><h3>Gate Envelope</h3>{render_table(['Gate','Runs','Scored','Frontier','Fastest','Slowest','Best SES'], gate_rows)}</section></section>"


def render_phase(data: dict[str, object], selected_phase: str | None) -> str:
    phase = next((item for item in data['phases'] if item['phase'] == selected_phase), None)
    if phase is None:
        phase = next((item for item in data['phases'] if item['done_rows']), None)
    if phase is None:
        return "<section class='panel empty'>No benchmark data found.</section>"
    filter_id = f"phase-{phase['phase']}"
    filters = render_filter_panel(filter_id, {'model': phase['models'], 'flow': phase['flows'], 'gate': phase['gates']})
    gate_pairs = build_delta_pairs(phase['done_rows'], 'gate_mode', ('model', 'flow', 'seed'), 'elapsed_s')
    flow_pairs = build_delta_pairs(phase['done_rows'], 'flow', ('model', 'gate_mode', 'seed'), 'elapsed_s')
    ses_pairs = build_delta_pairs(phase['scored_rows'], 'gate_mode', ('model', 'flow', 'seed'), 'ses_score')
    hit_pairs = build_delta_pairs(phase['scored_rows'], 'gate_mode', ('model', 'flow', 'seed'), 'hit_rate')
    insights = render_insight_cards(build_phase_insights(phase, gate_pairs, flow_pairs))
    guide = render_reading_guide([
        'Read Gate Delta and Flow Delta first to see whether the structural choice matters before you look at absolute scores.',
        'Use Seed strips to judge stability; wide spreads imply the same prompt/flow family is seed-sensitive.',
        'Only compare SES-side panels when score coverage is high enough; otherwise the ops panels are the safer read.',
    ])
    model_rows = [wrap_row([esc(row['group'][0]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ddg'], 3))}</span>"], {'filter-target': filter_id, 'model': row['group'][0]}) for row in phase['model_env']]
    flow_rows = [wrap_row([esc(row['group'][0]), esc(row['group'][1]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>"], {'filter-target': filter_id, 'model': row['group'][0], 'flow': row['group'][1]}) for row in phase['flow_env']]
    gate_rows = [wrap_row([esc(row['group'][0]), f"<span class='mono'>{row['runs']}</span>", f"<span class='mono'>{row['scored_runs']}</span>", f"<span class='mono'>{row['frontier_runs']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['fastest_s']))}</span>", f"<span class='mono'>{esc(fmt_seconds(row['slowest_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ses'], 4))}</span>"], {'filter-target': filter_id, 'gate': row['group'][0]}) for row in phase['gate_env']]
    scored_rows = [wrap_row([esc(row['model']), esc(row['flow']), esc(row['gate_mode']), f"<span class='mono'>{row['seed']}</span>", f"<span class='mono'>{esc(fmt_seconds(row['elapsed_s']))}</span>", f"<span class='mono'>{esc(fmt_num(row['ses_score'], 4))}</span>", f"<span class='mono'>{esc(fmt_num(row['best_ddg'], 3))}</span>", f"<span class='mono'>{esc(fmt_num(row['hit_rate'], 4))}</span>"], {'filter-target': filter_id, 'phase': row['phase'], 'model': row['model'], 'flow': row['flow'], 'gate': row['gate_mode']}) for row in sorted(phase['scored_rows'], key=lambda row: (str(row['run_name']) not in phase['frontier_ids'], row.get('elapsed_s') or 10**12, -(row.get('ses_score') or 0)))]
    raw_rows = [wrap_row([esc(row['model']), esc(row['flow']), esc(row['gate_mode']), f"<span class='mono'>{row['seed']}</span>", "<span class='status-pill %s'>%s</span>" % ('pending' if row['state'] != 'done' else '', esc(row['state'])), f"<span class='mono'>{esc(fmt_seconds(row['elapsed_s']))}</span>", f"<span class='mono'>{esc(row['status_path'])}</span>"], {'filter-target': filter_id, 'model': row['model'], 'flow': row['flow'], 'gate': row['gate_mode']}) for row in phase['raw_rows']]
    seeds = phase['heatmap_seeds']
    head = ''.join(f"<div class='heat-label heat-head'>seed {seed}</div>" for seed in seeds)
    peak = max((cell['elapsed_s'] or 0) for item in phase['heatmap_rows'] for cell in item['cells']) if phase['heatmap_rows'] else 1
    heat_rows = []
    for item in phase['heatmap_rows']:
        cells = []
        for cell in item['cells']:
            if cell['elapsed_s'] is None:
                bg = 'var(--heat-empty)'
            else:
                bg = 'rgba(56, 189, 248, %.2f)' % (0.16 + ((cell['elapsed_s'] or 0) / max(peak, 1)) * 0.48)
            cells.append(f"<div class='heat-cell' style='background:{bg}'><strong>{esc(fmt_seconds(cell['elapsed_s']))}</strong><span class='small-note'>{esc(cell['state'])}</span></div>")
        heat_rows.append("<div class='heatmap-row interactive-node' data-filter-target='" + filter_id + "' data-model='" + attr(item['model']) + "' data-flow='" + attr(item['flow']) + "' data-gate='" + attr(item['gate_mode']) + "' style='grid-template-columns:220px repeat(" + str(len(seeds)) + ", minmax(120px, 1fr));'><div class='heat-label'>" + esc(item['label']) + "</div>" + ''.join(cells) + "</div>")
    chip_html = ''.join(f"<span class='chip'>{esc(state)} <strong>{count}</strong></span>" for state, count in sorted(phase['state_counts'].items()))
    score_coverage = (len(phase['scored_rows']) / len(phase['done_rows'])) if phase['done_rows'] else 0.0
    runtime_first = score_coverage < 0.25
    score_sections = (
        f"<section class='grid-2'><section class='panel'><h3>Runtime vs SES</h3><p class='sub'>each dot is one scored run</p>{render_scatter(phase['scored_rows'], 'elapsed_s', 'ses_score', 'model', 'Runtime', 'SES', filter_id)}</section><section class='panel'><h3>Runtime vs best ddG</h3><p class='sub'>colored by gate mode</p>{render_scatter(phase['scored_rows'], 'elapsed_s', 'best_ddg', 'gate_mode', 'Runtime', 'best ddG', filter_id, maximize_y=False)}</section></section><section class='grid-2'><section class='panel'><h3>Gate SES Delta</h3><p class='sub'>same model, flow, seed with ses delta</p>{render_delta_chart(ses_pairs, filter_id, value_formatter=lambda value: fmt_num(value, 4), value_suffix='ses delta')}</section><section class='panel'><h3>Gate Hit-Rate Delta</h3><p class='sub'>same model, flow, seed with hit-rate delta</p>{render_delta_chart(hit_pairs, filter_id, value_formatter=lambda value: fmt_num(value, 4), value_suffix='hit-rate delta')}</section></section><section class='grid-2'><section class='panel'><h3>Seed SES Strip</h3><p class='sub'>seed-level SES spread, colored by gate</p>{render_seed_strip(phase['scored_rows'], 'ses_score', 'SES', filter_id)}</section><section class='panel'><h3>Runtime vs Hit Rate</h3><p class='sub'>run-level hit yield vs runtime</p>{render_scatter(phase['scored_rows'], 'elapsed_s', 'hit_rate', 'model', 'Runtime', 'Hit Rate', filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Runtime vs Improvement</h3><p class='sub'>run-level improvement vs runtime</p>{render_scatter(phase['scored_rows'], 'elapsed_s', 'improvement', 'gate_mode', 'Runtime', 'Improvement', filter_id)}</section><section class='panel'><h3>SES Subscores by Run</h3><p class='sub'>hit_rate, improvement, efficiency, diversity, robustness for each scored run</p>{render_component_strip(phase['scored_rows'], ('hit_rate', 'improvement', 'efficiency', 'diversity', 'robustness'), filter_id)}</section></section><section class='grid-2'><section class='panel'><h3>Frontier Contribution</h3>{render_frontier_contrib(phase['scored_rows'], phase['frontier_ids'], ('model', 'gate_mode'), filter_id)}</section><section class='panel'><h3>ddG Frontier Ledger</h3><p class='sub'>runtime x best ddG non-dominated runs in this phase</p>{render_ddg_frontier(phase['scored_rows'], filter_id)}</section></section><section class='panel'><h3>Scored Run Ledger</h3>{render_table(['Model','Flow','Gate','Seed','Runtime','SES','best ddG','Hit Rate'], scored_rows)}</section>"
        if phase['scored_rows']
        else f"<section class='grid-2'><section class='panel'><h3>Flow Runtime Strip</h3><p class='sub'>completed-run runtime spread, colored by flow</p>{render_seed_strip(phase['done_rows'], 'elapsed_s', 'Runtime', filter_id, color_key='flow')}</section><section class='panel'><h3>Gate Runtime Strip</h3><p class='sub'>completed-run runtime spread, colored by gate</p>{render_seed_strip(phase['done_rows'], 'elapsed_s', 'Runtime', filter_id, color_key='gate_mode')}</section></section><section class='grid-2'><section class='panel'><h3>Phase Coverage Matrix</h3><p class='sub'>model / flow / gate by seed coverage</p>{render_coverage_matrix(phase['raw_rows'], ('model', 'flow', 'gate_mode'), filter_id)}</section><section class='panel'><h3>Runtime-Only Phase</h3><p class='sub'>this phase has no SES files yet, so the view pivots to operations and flow comparison.</p><div class='chips'><span class='chip'>Completed <strong>{len(phase['done_rows'])}</strong></span><span class='chip'>Run Dirs <strong>{len(phase['raw_rows'])}</strong></span><span class='chip'>Flows <strong>{len(phase['flows'])}</strong></span><span class='chip'>Gates <strong>{len(phase['gates'])}</strong></span></div></section></section>"
    )
    _phase_title = 'Runtime-Heavy Phase' if runtime_first else 'Runtime-Only Phase'
    _phase_desc = 'SES coverage is sparse, so runtime and flow comparison are prioritized ahead of the score panels.' if runtime_first else 'this phase has no SES files yet, so the view pivots to operations and flow comparison.'
    ops_sections = f"<section class='grid-2'><section class='panel'><h3>Flow Runtime Strip</h3><p class='sub'>completed-run runtime spread, colored by flow</p>{render_seed_strip(phase['done_rows'], 'elapsed_s', 'Runtime', filter_id, color_key='flow')}</section><section class='panel'><h3>Gate Runtime Strip</h3><p class='sub'>completed-run runtime spread, colored by gate</p>{render_seed_strip(phase['done_rows'], 'elapsed_s', 'Runtime', filter_id, color_key='gate_mode')}</section></section><section class='grid-2'><section class='panel'><h3>Phase Coverage Matrix</h3><p class='sub'>model / flow / gate by seed coverage</p>{render_coverage_matrix(phase['raw_rows'], ('model', 'flow', 'gate_mode'), filter_id)}</section><section class='panel'><h3>{_phase_title}</h3><p class='sub'>{_phase_desc}</p><div class='chips'><span class='chip'>Completed <strong>{len(phase['done_rows'])}</strong></span><span class='chip'>Scored <strong>{len(phase['scored_rows'])}</strong></span><span class='chip'>Coverage <strong>{score_coverage:.0%}</strong></span><span class='chip'>Flows <strong>{len(phase['flows'])}</strong></span></div></section></section>"
    main_sections = ops_sections + score_sections if runtime_first else score_sections
    return f"<section class='hero'><div class='hero-top'><div><span class='badge'>LLM Benchmark Observatory</span><h1>Phase Detail: {esc(phase['phase'])}</h1><p><span class='mono'>{esc(data['outputs_root'])}</span> phase trade-off view without averages.</p></div></div><section class='kpis'><article class='kpi'><div class='eyebrow'>Run Dirs</div><div class='value'>{len(phase['raw_rows'])}</div></article><article class='kpi'><div class='eyebrow'>Completed</div><div class='value'>{len(phase['done_rows'])}</div></article><article class='kpi'><div class='eyebrow'>Scored</div><div class='value'>{len(phase['scored_rows'])}</div></article><article class='kpi'><div class='eyebrow'>Runtime Span</div><div class='value'>{esc(fmt_seconds(phase['runtime_span']['min']))}</div><div class='caption'>{esc(fmt_seconds(phase['runtime_span']['min']))} -> {esc(fmt_seconds(phase['runtime_span']['max']))}</div></article></section></section>{filters}<section class='grid-2'><section class='panel panel-hero-copy'><h3>Quick Read</h3><p class='sub'>phase-specific interpretation without collapsing runs into averages</p>{insights}</section><section class='panel'><h3>How To Read This Phase</h3><p class='sub'>the minimum path to a sane comparison</p>{guide}</section></section><section class='grid-2'><section class='panel'><h3>Gate Delta Dumbbell</h3><p class='sub'>same model, flow, seed with static vs adaptive</p>{render_delta_chart(gate_pairs, filter_id, value_suffix='runtime delta')}</section><section class='panel'><h3>Flow Delta Dumbbell</h3><p class='sub'>same model, gate, seed with flow deltas</p>{render_delta_chart(flow_pairs, filter_id, value_suffix='runtime delta')}</section></section><section class='panel'><h3>Seed Runtime Strip</h3><p class='sub'>seed-level runtime spread, colored by gate</p>{render_seed_strip(phase['done_rows'], 'elapsed_s', 'Runtime', filter_id)}</section>{main_sections}<section class='grid-3'><section class='panel'><h3>LLM Envelope</h3>{render_table(['Model','Runs','Scored','Frontier','Fastest','Slowest','Best SES','Best ddG'], model_rows)}</section><section class='panel'><h3>Flow Envelope</h3>{render_table(['Model','Flow','Runs','Scored','Frontier','Fastest','Slowest','Best SES'], flow_rows)}</section><section class='panel'><h3>Gate Envelope</h3>{render_table(['Gate','Runs','Scored','Frontier','Fastest','Slowest','Best SES'], gate_rows)}</section></section><section class='panel'><h3>Run State Coverage</h3><div class='chips'>{chip_html}</div><div class='heatmap' style='margin-top:14px;'><div class='heatmap-row' style='grid-template-columns:220px repeat({len(seeds)}, minmax(120px, 1fr));'><div></div>{head}</div>{''.join(heat_rows)}</div></section><section class='panel'><h3>Raw Run Ledger</h3>{render_table(['Model','Flow','Gate','Seed','State','Elapsed','Status'], raw_rows)}</section>"


def render_html(data: dict[str, object], query: dict[str, list[str]]) -> str:
    current_view = query.get('view', ['overview'])[0]
    current_phase = query.get('phase', [None])[0]
    content = render_overview(data) if current_view == 'overview' else render_phase(data, current_phase)
    nav = render_nav(data, current_view, current_phase)
    script = """
<script>
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem('llm-benchmark-theme');
  if (saved) root.dataset.theme = saved;
  const compactSaved = localStorage.getItem('llm-benchmark-compact');
  if (compactSaved === '1') document.body.dataset.compact = '1';

  document.addEventListener('click', function (event) {
    const compactButton = event.target.closest('#compact-toggle');
    if (compactButton) {
      const enabled = document.body.dataset.compact === '1';
      if (enabled) {
        delete document.body.dataset.compact;
        localStorage.removeItem('llm-benchmark-compact');
      } else {
        document.body.dataset.compact = '1';
        localStorage.setItem('llm-benchmark-compact', '1');
      }
      return;
    }
    const exportButton = event.target.closest('#export-snapshot');
    if (exportButton) {
      const blob = new Blob([document.documentElement.outerHTML], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'llm-benchmark-' + (new URLSearchParams(location.search).get('phase') || new URLSearchParams(location.search).get('view') || 'snapshot') + '.html';
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 0);
      return;
    }
    const themeButton = event.target.closest('#theme-toggle');
    if (themeButton) {
      const next = root.dataset.theme === 'light' ? 'dark' : 'light';
      root.dataset.theme = next;
      localStorage.setItem('llm-benchmark-theme', next);
      return;
    }
    const resetButton = event.target.closest('.filter-reset');
    if (!resetButton) return;
    const panel = resetButton.closest('[data-filter-root]');
    if (!panel) return;
    panel.querySelectorAll('input[type="checkbox"]').forEach(function (input) { input.checked = true; });
    applyFilters(panel.dataset.filterRoot);
  });


  function getSelections(rootId) {
    const panel = document.querySelector('[data-filter-root="' + rootId + '"]');
    const selected = {};
    if (!panel) return selected;
    panel.querySelectorAll('input[type="checkbox"]').forEach(function (input) {
      const key = input.dataset.filterKey;
      selected[key] = selected[key] || [];
      if (input.checked) selected[key].push(input.value);
    });
    return selected;
  }


  function bindFilterPanels() {
    document.querySelectorAll('[data-filter-root]').forEach(function (panel) {
      const rootId = panel.dataset.filterRoot;
      panel.querySelectorAll('input[type="checkbox"]').forEach(function (input) {
        input.addEventListener('change', function () {
          applyFilters(rootId);
        });
        input.addEventListener('input', function () {
          applyFilters(rootId);
        });
      });
      panel.querySelectorAll('.filter-chip').forEach(function (chip) {
        chip.addEventListener('click', function () {
          setTimeout(function () { applyFilters(rootId); }, 0);
        });
      });
    });
  }

  function matches(el, selected) {
    return Object.keys(selected).every(function (key) {
      if (!selected[key].length) return false;
      const value = el.dataset[key];
      if (typeof value === 'undefined') return true;
      const parts = String(value).split('|');
      return (el.dataset.filterMode || 'any') === 'all'
        ? parts.every(function (part) { return selected[key].includes(part); })
        : parts.some(function (part) { return selected[key].includes(part); });
    });
  }




  let pinnedFocus = null;
  let tooltip = null;
  let compareTray = null;
  let dragState = null;

  function ensureTooltip() {
    if (tooltip) return tooltip;
    tooltip = document.createElement('div');
    tooltip.className = 'ui-tooltip';
    document.body.appendChild(tooltip);
    return tooltip;
  }

  function extractIdentity(el) {
    const keys = ['phase', 'model', 'flow', 'gate'];
    const ident = {};
    keys.forEach(function (key) {
      if (el.dataset[key]) ident[key] = el.dataset[key];
    });
    return ident;
  }

  function datasetMatches(el, ident) {
    return Object.keys(ident).every(function (key) {
      if (!el.dataset[key]) return false;
      return String(el.dataset[key]).split('|').includes(String(ident[key]));
    });
  }

  function clearFocus() {
    document.querySelectorAll('.interactive-match, .interactive-focus').forEach(function (el) {
      el.classList.remove('interactive-match', 'interactive-focus');
    });
  }

  function applyFocus(source) {
    clearFocus();
    if (!source) return;
    const ident = extractIdentity(source);
    document.querySelectorAll('.interactive-node').forEach(function (el) {
      if (datasetMatches(el, ident)) el.classList.add('interactive-match');
    });
    source.classList.add('interactive-focus');
  }

  function showTooltip(target, event) {
    const tip = target.dataset.tip;
    if (!tip) return;
    const el = ensureTooltip();
    el.textContent = tip;
    el.style.display = 'block';
    el.style.left = event.clientX + 14 + 'px';
    el.style.top = event.clientY + 14 + 'px';
  }

  function hideTooltip() {
    if (tooltip) tooltip.style.display = 'none';
  }

  function ensureCompareTray() {
    if (compareTray) return compareTray;
    compareTray = document.createElement('aside');
    compareTray.className = 'compare-tray';
    compareTray.innerHTML = '<div class="compare-head"><strong>Compare Tray</strong><div class="compare-actions"><button type="button" data-compare-action="copy">Copy</button><button type="button" data-compare-action="clear">Clear</button></div></div><div class="compare-note small-note">Ctrl/Cmd+click any point, row, or heatmap lane to add it here.</div><div class="compare-list"></div>';
    document.body.appendChild(compareTray);
    return compareTray;
  }

  function getCompareItems() {
    try {
      return JSON.parse(localStorage.getItem('llm-benchmark-compare') || '[]');
    } catch (error) {
      return [];
    }
  }

  function setCompareItems(items) {
    localStorage.setItem('llm-benchmark-compare', JSON.stringify(items.slice(0, 8)));
    renderCompareTray();
  }

  function renderCompareTray() {
    const tray = ensureCompareTray();
    const items = getCompareItems();
    tray.classList.toggle('is-empty', items.length === 0);
    const list = tray.querySelector('.compare-list');
    list.innerHTML = items.length
      ? items.map(function (item) { return '<div class="compare-item"><button type="button" class="compare-remove" data-compare-remove="' + item.id + '">x</button><div>' + item.label + '</div></div>'; }).join('')
      : '<div class="small-note">No pinned comparisons.</div>';
  }

  function toggleCompareItem(target) {
    const label = target.dataset.tip;
    if (!label) return;
    const id = [target.dataset.phase || '', target.dataset.model || '', target.dataset.flow || '', target.dataset.gate || '', label].join('|');
    const items = getCompareItems();
    const index = items.findIndex(function (item) { return item.id === id; });
    if (index >= 0) items.splice(index, 1);
    else items.unshift({ id: id, label: label });
    setCompareItems(items);
  }

  function getPointCenter(el) {
    const cx = Number(el.getAttribute('cx'));
    const cy = Number(el.getAttribute('cy'));
    return Number.isFinite(cx) && Number.isFinite(cy) ? { x: cx, y: cy } : null;
  }

  function addCompareItemsFromTargets(targets) {
    const existing = getCompareItems();
    const map = new Map(existing.map(function (item) { return [item.id, item]; }));
    targets.forEach(function (target) {
      const label = target.dataset.tip;
      if (!label) return;
      const id = [target.dataset.phase || '', target.dataset.model || '', target.dataset.flow || '', target.dataset.gate || '', label].join('|');
      map.set(id, { id: id, label: label });
    });
    setCompareItems(Array.from(map.values()));
  }

  function ensureSelectionRect(svg) {
    let rect = svg.querySelector('.selection-rect');
    if (rect) return rect;
    rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('class', 'selection-rect');
    rect.setAttribute('display', 'none');
    svg.appendChild(rect);
    return rect;
  }

  function svgPoint(svg, event) {
    const pt = svg.createSVGPoint();
    pt.x = event.clientX;
    pt.y = event.clientY;
    const converted = pt.matrixTransform(svg.getScreenCTM().inverse());
    return { x: converted.x, y: converted.y };
  }

  function updateFilterSummary(rootId, selected) {
    const panel = document.querySelector('[data-filter-root="' + rootId + '"]');
    if (!panel) return;
    const summary = panel.querySelector('.filter-active');
    if (!summary) return;
    const parts = [];
    Object.keys(selected).forEach(function (key) {
      const total = panel.querySelectorAll('input[data-filter-key="' + key + '"]').length;
      const active = selected[key].length;
      if (active === total) return;
      parts.push(key + ': ' + active + '/' + total);
    });
    summary.textContent = parts.length ? 'Active filters: ' + parts.join(' | ') : 'All values active';
  }

  function updatePanelState(rootId) {
    document.querySelectorAll('.panel').forEach(function (panel) {
      if (panel.matches('[data-filter-root]')) return;
      const targets = Array.from(panel.querySelectorAll('[data-filter-target="' + rootId + '"]'));
      if (!targets.length) return;
      const anyVisible = targets.some(function (el) { return el.style.display !== 'none'; });
      panel.classList.toggle('filtered-empty', !anyVisible);
      let notice = panel.querySelector('.panel-empty-note');
      if (!anyVisible) {
        if (!notice) {
          notice = document.createElement('div');
          notice.className = 'panel-empty-note small-note';
          notice.textContent = 'Current filters hide all rows in this panel.';
          panel.appendChild(notice);
        }
      } else if (notice) {
        notice.remove();
      }
    });
  }

  function applyFilters(rootId) {
    const selected = getSelections(rootId);
    document.querySelectorAll('[data-filter-target="' + rootId + '"]').forEach(function (el) {
      const visible = matches(el, selected);
      el.classList.toggle('filter-hidden', !visible);
      if (el instanceof SVGElement) {
        el.setAttribute('display', visible ? 'inline' : 'none');
        el.setAttribute('visibility', visible ? 'visible' : 'hidden');
      } else {
        el.style.display = visible ? '' : 'none';
        el.style.visibility = visible ? '' : 'hidden';
      }
      el.style.opacity = visible ? '' : '0';
      el.style.pointerEvents = visible ? '' : 'none';
    });
    updateFilterSummary(rootId, selected);
    updatePanelState(rootId);
  }

  function updateLegendState(scope) {
    if (!scope) return;
    const hiddenMap = {};
    scope.querySelectorAll('.legend-item.is-off').forEach(function (item) {
      const key = item.dataset.legendKey;
      hiddenMap[key] = hiddenMap[key] || new Set();
      hiddenMap[key].add(item.dataset.legendValue);
    });
    scope.querySelectorAll('.interactive-node').forEach(function (el) {
      let hidden = false;
      Object.keys(hiddenMap).forEach(function (key) {
        const value = el.dataset[key];
        if (value && hiddenMap[key].has(value)) hidden = true;
      });
      el.style.opacity = hidden ? '0.12' : '';
      if (hidden && el.classList.contains('interactive-focus')) el.classList.remove('interactive-focus');
    });
  }

  document.addEventListener('click', function (event) {
    const compareAction = event.target.closest('[data-compare-action]');
    if (compareAction) {
      if (compareAction.dataset.compareAction === 'clear') setCompareItems([]);
      if (compareAction.dataset.compareAction === 'copy') {
        navigator.clipboard.writeText(getCompareItems().map(function (item) { return item.label; }).join(String.fromCharCode(10)));
      }
      return;
    }
    const compareRemove = event.target.closest('[data-compare-remove]');
    if (compareRemove) {
      setCompareItems(getCompareItems().filter(function (item) { return item.id !== compareRemove.dataset.compareRemove; }));
      return;
    }
    const legendButton = event.target.closest('.legend-item');
    if (legendButton) {
      legendButton.classList.toggle('is-off');
      updateLegendState(legendButton.closest('.viz-shell'));
      return;
    }
  });

  document.addEventListener('mouseover', function (event) {
    const target = event.target.closest('.interactive-node');
    if (!target) return;
    if (!pinnedFocus) applyFocus(target);
    showTooltip(target, event);
  });

  document.addEventListener('mousemove', function (event) {
    const target = event.target.closest('.interactive-node');
    if (!target) return;
    showTooltip(target, event);
  });

  document.addEventListener('mouseout', function (event) {
    const target = event.target.closest('.interactive-node');
    if (!target) return;
    hideTooltip();
    if (!pinnedFocus) clearFocus();
  });

  document.addEventListener('click', function (event) {
    const target = event.target.closest('.interactive-node');
    if (!target) return;
    if (event.ctrlKey || event.metaKey) {
      toggleCompareItem(target);
      showTooltip(target, event);
      return;
    }
    if (pinnedFocus === target) {
      pinnedFocus = null;
      clearFocus();
      hideTooltip();
      return;
    }
    pinnedFocus = target;
    applyFocus(target);
    showTooltip(target, event);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      pinnedFocus = null;
      clearFocus();
      hideTooltip();
    }
  });

  document.addEventListener('mousedown', function (event) {
    const svg = event.target.closest('svg.chart-svg');
    if (!svg || !event.shiftKey) return;
    dragState = { svg: svg, start: svgPoint(svg, event) };
    const rect = ensureSelectionRect(svg);
    rect.setAttribute('x', String(dragState.start.x));
    rect.setAttribute('y', String(dragState.start.y));
    rect.setAttribute('width', '0');
    rect.setAttribute('height', '0');
    rect.setAttribute('display', 'block');
    event.preventDefault();
  });

  document.addEventListener('mousemove', function (event) {
    if (!dragState) return;
    const point = svgPoint(dragState.svg, event);
    const x = Math.min(dragState.start.x, point.x);
    const y = Math.min(dragState.start.y, point.y);
    const width = Math.abs(point.x - dragState.start.x);
    const height = Math.abs(point.y - dragState.start.y);
    const rect = ensureSelectionRect(dragState.svg);
    rect.setAttribute('x', String(x));
    rect.setAttribute('y', String(y));
    rect.setAttribute('width', String(width));
    rect.setAttribute('height', String(height));
  });

  document.addEventListener('mouseup', function (event) {
    if (!dragState) return;
    const point = svgPoint(dragState.svg, event);
    const x1 = Math.min(dragState.start.x, point.x);
    const x2 = Math.max(dragState.start.x, point.x);
    const y1 = Math.min(dragState.start.y, point.y);
    const y2 = Math.max(dragState.start.y, point.y);
    const rect = ensureSelectionRect(dragState.svg);
    rect.setAttribute('display', 'none');
    const selected = Array.from(dragState.svg.querySelectorAll('circle.interactive-node')).filter(function (el) {
      const center = getPointCenter(el);
      return center && center.x >= x1 && center.x <= x2 && center.y >= y1 && center.y <= y2 && el.style.display !== 'none' && el.style.opacity !== '0.12';
    });
    if (selected.length) addCompareItemsFromTargets(selected);
    dragState = null;
  });

  bindFilterPanels();
  document.querySelectorAll('[data-filter-root]').forEach(function (panel) {
    applyFilters(panel.dataset.filterRoot);
  });
  renderCompareTray();
}());
"""
    return f"<!doctype html><html lang='ko'><head><meta charset='UTF-8' /><meta name='viewport' content='width=device-width, initial-scale=1.0' /><title>LLM Benchmark Observatory</title><link rel='stylesheet' href='/styles.css' /></head><body><div class='page-wrap'>{nav}{content}</div>{script}</body></html>"


class Handler(BaseHTTPRequestHandler):
    def send_payload(self, payload: bytes, content_type: str, include_body: bool = True) -> None:
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def do_HEAD(self):
        self.handle_request(include_body=False)

    def do_GET(self):
        self.handle_request(include_body=True)

    def handle_request(self, include_body: bool = True):
        parsed = urlparse(self.path)
        if parsed.path == '/api/overview':
            payload = json.dumps(collect_data(), ensure_ascii=False, default=lambda o: sorted(o) if isinstance(o, set) else str(o)).encode('utf-8')
            self.send_payload(payload, 'application/json; charset=utf-8', include_body)
            return
        if parsed.path == '/api/results':
            results_file = OUTPUTS_DIR / '_all_results.json'
            if results_file.exists():
                payload = results_file.read_bytes()
            else:
                payload = b'[]'
            self.send_payload(payload, 'application/json; charset=utf-8', include_body)
            return
        if parsed.path == '/dashboard':
            dash_file = Path(__file__).parent / 'results_dashboard.html'
            if dash_file.exists():
                content = dash_file.read_bytes()
                self.send_payload(content, 'text/html; charset=utf-8', include_body)
                return
            self.send_error(404)
            return
        if parsed.path in ('/', ''):
            content = render_html(collect_data(), parse_qs(parsed.query)).encode('utf-8')
            self.send_payload(content, 'text/html; charset=utf-8', include_body)
            return
        rel_path = parsed.path.lstrip('/')
        file_path = (STATIC_DIR / rel_path).resolve()
        try:
            file_path.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or 'text/plain'
        self.send_payload(content, f'{content_type}; charset=utf-8', include_body)


def main() -> None:
    parser = argparse.ArgumentParser(description='Standalone UI for llm_benchmark outputs')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f'Benchmark UI: http://{args.host}:{args.port}')
    server.serve_forever()


if __name__ == '__main__':
    main()
