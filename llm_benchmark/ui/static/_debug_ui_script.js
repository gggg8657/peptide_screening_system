
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

  document.addEventListener('change', function (event) {
    const input = event.target;
    if (!(input instanceof HTMLInputElement)) return;
    if (input.type !== 'checkbox' || !input.dataset.filterKey) return;
    const panel = input.closest('[data-filter-root]');
    if (!panel) return;
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

  function matches(el, selected) {
    return Object.keys(selected).every(function (key) {
      if (!selected[key].length) return false;
      const value = el.dataset[key];
      if (typeof value === 'undefined') return true;
      return String(value).split('|').some(function (part) { return selected[key].includes(part); });
    });
  }


  function matchesRow(row, selected) {
    return Object.keys(selected).every(function (key) {
      if (!selected[key].length) return false;
      const value = row[key];
      if (typeof value === 'undefined') return true;
      return String(value).split('|').some(function (part) { return selected[key].includes(part); });
    });
  }

  function getThemeValue(name, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  }

  function buildPlotlyLayout(spec) {
    return {
      autosize: true,
      height: spec.kind === 'component' ? 360 : 420,
      margin: { l: 72, r: 18, t: 18, b: 54 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: getThemeValue('--text', '#ecf4ff'), family: 'IBM Plex Sans, Pretendard, Segoe UI, sans-serif', size: 12 },
      xaxis: { title: spec.xLabel, gridcolor: getThemeValue('--border', 'rgba(148,163,184,0.16)'), zeroline: false },
      yaxis: { title: spec.kind === 'scatter' ? spec.yLabel : '', gridcolor: getThemeValue('--border', 'rgba(148,163,184,0.16)'), zeroline: false, autorange: spec.reverseY ? 'reversed' : true, categoryorder: 'array' },
      legend: { orientation: 'h', y: -0.18, x: 0 },
      hoverlabel: { bgcolor: getThemeValue('--panel-strong', '#08151c'), bordercolor: getThemeValue('--border', 'rgba(148,163,184,0.16)') },
    };
  }

  function renderPlotlyChart(container, selected) {
    if (!window.Plotly) {
      container.innerHTML = '<div class="empty">Plotly failed to load.</div>';
      return;
    }
    try {
      const spec = JSON.parse(container.dataset.plotSpec);
      const rows = spec.rows.filter(function (row) { return matchesRow(row, selected); });
      const groups = new Map();
      rows.forEach(function (row) {
        const key = row.color || 'unknown';
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(row);
      });
      const palette = ['#38bdf8', '#2dd4bf', '#f59e0b', '#fb7185', '#a78bfa', '#f97316', '#22c55e', '#eab308'];
      const traces = Array.from(groups.entries()).map(function (entry, index) {
        const label = entry[0];
        const items = entry[1];
        return {
          type: 'scatter',
          mode: 'markers',
          name: label,
          x: items.map(function (row) { return row.x; }),
          y: items.map(function (row) { return row.y; }),
          text: items.map(function (row) { return row.phase + ' | ' + row.model + ' | ' + row.flow + ' | ' + row.gate + ' | seed ' + row.seed; }),
          hovertemplate: '%{text}<br>' + (spec.kind === 'scatter' ? (spec.xLabel + ': %{x:.2f}<br>' + spec.yLabel + ': %{y:.4f}<extra></extra>') : (spec.xLabel + ': %{x:.4f}<br>%{y}<extra></extra>')),
          marker: {
            size: 10,
            color: palette[index % palette.length],
            opacity: 0.9,
            line: { width: 1, color: palette[index % palette.length] },
            symbol: spec.kind === 'component' ? 'circle' : 'circle',
          },
        };
      });
      const layout = buildPlotlyLayout(spec);
      if (spec.kind !== 'scatter') {
        const categories = [];
        rows.forEach(function (row) { if (!categories.includes(row.y)) categories.push(row.y); });
        layout.yaxis.categoryarray = categories;
      }
      if (!rows.length) {
        Plotly.react(container, [], Object.assign(layout, { annotations: [{ text: 'No rows for current filters', x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', showarrow: false, font: { color: getThemeValue('--muted', '#94a3b8'), size: 14 } }] }), { displayModeBar: false, responsive: true });
        container.dataset.plotCount = '0';
        return;
      }
      Plotly.react(container, traces, layout, { displayModeBar: false, responsive: true });
      container.dataset.plotCount = String(rows.length);
    } catch (error) {
      container.innerHTML = '<div class="empty">Plot render failed: ' + String(error && error.message ? error.message : error) + '</div>';
    }
  }

  function renderPlotlyCharts(rootId, selected) {
    document.querySelectorAll('[data-plot-root="' + rootId + '"]').forEach(function (container) {
      renderPlotlyChart(container, selected);
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
    renderPlotlyCharts(rootId, selected);
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
        navigator.clipboard.writeText(getCompareItems().map(function (item) { return item.label; }).join('\n'));
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

  document.querySelectorAll('[data-filter-root]').forEach(function (panel) {
    applyFilters(panel.dataset.filterRoot);
  });
  renderCompareTray();
}());
