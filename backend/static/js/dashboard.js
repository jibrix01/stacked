(function () {
  const panel = document.getElementById('dashboard-panel');
  const tabButtons = document.querySelectorAll('#tab-select button');

  let activeCharts = [];
  const sectionCache = {};

  function destroyCharts() {
    activeCharts.forEach((c) => c.destroy());
    activeCharts = [];
  }

  function el(tag, className, html) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (html !== undefined) node.innerHTML = html;
    return node;
  }

  function statBox(value, label) {
    const box = el('div', 'stat-box');
    box.appendChild(el('div', 'value num', value));
    box.appendChild(el('div', 'label', label));
    return box;
  }

  function chartCard(title, canvasHeightClass, full) {
    const card = el('div', 'card' + (full ? ' full' : ''));
    card.appendChild(el('div', 'card-title', title));
    const wrap = el('div', 'chart-canvas-wrap' + (canvasHeightClass ? ' ' + canvasHeightClass : ''));
    const canvas = document.createElement('canvas');
    wrap.appendChild(canvas);
    card.appendChild(wrap);
    return { card, canvas };
  }

  function makeChart(canvas, config) {
    const chart = new Chart(canvas.getContext('2d'), config);
    activeCharts.push(chart);
    return chart;
  }

  // ---------- Section renderers ----------

  function renderOverview(data) {
    const wrap = el('div');

    const stats = el('div', 'stat-row');
    stats.appendChild(statBox(data.audit.total_raw_responses.toLocaleString(), 'Raw responses'));
    stats.appendChild(statBox(`${data.audit.professional_developers.toLocaleString()} (${data.audit.professional_pct}%)`, 'Professional developers'));
    stats.appendChild(statBox(data.audit.cleaned_rows.toLocaleString(), 'Rows after cleaning'));
    wrap.appendChild(stats);

    const grid = el('div', 'chart-grid');
    wrap.appendChild(grid);

    const c1 = chartCard('Annual compensation (raw)');
    grid.appendChild(c1.card);
    const c2 = chartCard('Annual compensation (log10)');
    grid.appendChild(c2.card);
    const c3 = chartCard('Years of professional experience');
    grid.appendChild(c3.card);
    const c4 = chartCard('Respondents by country (top 10)');
    grid.appendChild(c4.card);
    const c5 = chartCard('Remote work distribution');
    grid.appendChild(c5.card);
    const c6 = chartCard('Education level distribution');
    grid.appendChild(c6.card);

    panel.innerHTML = '';
    panel.appendChild(wrap);

    const histOpts = (xLabel) => ChartTheme.baseOptions({
      plugins: { legend: { display: false } },
      scales: {
        x: {
          title: { display: true, text: xLabel, color: ChartTheme.text },
          ticks: {
            color: ChartTheme.text,
            maxRotation: 0,
            minRotation: 0,
            callback: function(val, index, ticks) {
              const step = Math.ceil(ticks.length / 8);
              if (index % step === 0) {
                return this.getLabelForValue(val);
              }
              return '';
            }
          },
          grid: { display: false }
        },
        y: { ticks: { color: ChartTheme.text }, grid: { color: ChartTheme.grid } },
      },
    });

    makeChart(c1.canvas, {
      type: 'bar',
      data: { labels: data.histograms.comp_raw.bin_centers.map((v) => ChartTheme.fmtUsd(v)), datasets: [{ data: data.histograms.comp_raw.counts, backgroundColor: ChartTheme.purple, barPercentage: 1, categoryPercentage: 1 }] },
      options: histOpts('USD'),
    });
    makeChart(c2.canvas, {
      type: 'bar',
      data: { labels: data.histograms.comp_log10.bin_centers, datasets: [{ data: data.histograms.comp_log10.counts, backgroundColor: ChartTheme.purpleLight, barPercentage: 1, categoryPercentage: 1 }] },
      options: histOpts('log10(USD)'),
    });
    makeChart(c3.canvas, {
      type: 'bar',
      data: { labels: data.histograms.experience_years.bin_centers, datasets: [{ data: data.histograms.experience_years.counts, backgroundColor: ChartTheme.purple, barPercentage: 1, categoryPercentage: 1 }] },
      options: histOpts('Years'),
    });
    makeChart(c4.canvas, {
      type: 'bar',
      data: { labels: Object.keys(data.top10_countries), datasets: [{ data: Object.values(data.top10_countries), backgroundColor: ChartTheme.purpleLight }] },
      options: ChartTheme.baseOptions({ indexAxis: 'y', plugins: { legend: { display: false } } }),
    });
    makeChart(c5.canvas, {
      type: 'doughnut',
      data: { labels: Object.keys(data.remote_work_distribution), datasets: [{ data: Object.values(data.remote_work_distribution), backgroundColor: ChartTheme.palette }] },
      options: ChartTheme.baseOptions({ scales: {} }),
    });
    makeChart(c6.canvas, {
      type: 'bar',
      data: { labels: Object.keys(data.ed_level_distribution).map((l) => l.length > 22 ? l.slice(0, 22) + '\u2026' : l), datasets: [{ data: Object.values(data.ed_level_distribution), backgroundColor: ChartTheme.purple }] },
      options: ChartTheme.baseOptions({ indexAxis: 'y', plugins: { legend: { display: false } } }),
    });
  }

  function renderPayByCountry(data) {
    const wrap = el('div');
    const grid = el('div', 'chart-grid');
    wrap.appendChild(grid);

    const c1 = chartCard('Experience vs. pay, by country (log scale)', 'tall', true);
    grid.appendChild(c1.card);
    const c2 = chartCard('Median pay by country');
    grid.appendChild(c2.card);
    const c3 = chartCard('US pay by remote status');
    grid.appendChild(c3.card);

    panel.innerHTML = '';
    panel.appendChild(wrap);

    const countries = Object.keys(data.scatter_by_country);
    const scatterDatasets = countries.map((country, i) => ({
      label: country,
      data: data.scatter_by_country[country],
      backgroundColor: ChartTheme.palette[i % ChartTheme.palette.length],
      pointRadius: 2.5,
      type: 'scatter',
    }));
    const trendDatasets = countries.map((country, i) => ({
      label: country + ' trend',
      data: data.trendline_by_country[country],
      type: 'line',
      borderColor: ChartTheme.palette[i % ChartTheme.palette.length],
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
    }));

    makeChart(c1.canvas, {
      type: 'scatter',
      data: { datasets: [...scatterDatasets, ...trendDatasets] },
      options: ChartTheme.baseOptions({
        plugins: {
          legend: { labels: { color: ChartTheme.text, filter: (item) => !item.text.endsWith('trend') } },
          tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ChartTheme.fmtUsd(ctx.raw.y)} @ ${ctx.raw.x}y` } },
        },
        scales: {
          x: { title: { display: true, text: 'Years experience', color: ChartTheme.text }, ticks: { color: ChartTheme.text }, grid: { color: ChartTheme.grid } },
          y: { type: 'logarithmic', title: { display: true, text: 'Annual salary (USD, log)', color: ChartTheme.text }, ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtUsd(v) }, grid: { color: ChartTheme.grid } },
        },
      }),
    });

    makeChart(c2.canvas, {
      type: 'bar',
      data: { labels: Object.keys(data.median_pay_by_country), datasets: [{ data: Object.values(data.median_pay_by_country), backgroundColor: ChartTheme.purple }] },
      options: ChartTheme.baseOptions({
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ChartTheme.fmtUsd(ctx.raw) } } },
        scales: { x: { ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtUsd(v) }, grid: { color: ChartTheme.grid } }, y: { ticks: { color: ChartTheme.text }, grid: { display: false } } },
      }),
    });

    makeChart(c3.canvas, {
      type: 'bar',
      data: {
        labels: data.remote_work_us.map((r) => r.RemoteWork),
        datasets: [{ label: 'Median comp (USD)', data: data.remote_work_us.map((r) => r.median_comp), backgroundColor: ChartTheme.purpleLight }],
      },
      options: ChartTheme.baseOptions({
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ChartTheme.fmtUsd(ctx.raw) } } },
        scales: { x: { ticks: { color: ChartTheme.text, maxRotation: 0, autoSkip: false, font: { size: 9 } }, grid: { display: false } }, y: { ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtUsd(v) }, grid: { color: ChartTheme.grid } } },
      }),
    });
  }

  function renderLanguages(data) {
    const wrap = el('div');
    const grid = el('div', 'chart-grid');
    wrap.appendChild(grid);

    const c1 = chartCard('Median pay vs. median experience (bubble = developer count)', 'tall', true);
    grid.appendChild(c1.card);
    const c2 = chartCard('Median pay by language, top 20', 'tall', true);
    grid.appendChild(c2.card);

    panel.innerHTML = '';
    panel.appendChild(wrap);

    const stats = data.language_stats;
    makeChart(c1.canvas, {
      type: 'bubble',
      data: {
        datasets: [{
          data: stats.map((s) => ({ x: s.median_exp, y: s.median_comp, r: Math.max(4, Math.sqrt(s.developer_count) / 4), label: s.Language })),
          backgroundColor: 'rgba(139, 92, 246, 0.55)',
          borderColor: ChartTheme.purple,
        }],
      },
      options: ChartTheme.baseOptions({
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => `${ctx.raw.label}: ${ChartTheme.fmtUsd(ctx.raw.y)}, ${ctx.raw.x}y exp` } },
        },
        scales: {
          x: { title: { display: true, text: 'Median years experience', color: ChartTheme.text }, ticks: { color: ChartTheme.text }, grid: { color: ChartTheme.grid } },
          y: { title: { display: true, text: 'Median comp (USD)', color: ChartTheme.text }, ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtUsd(v) }, grid: { color: ChartTheme.grid } },
        },
      }),
      plugins: [{
        id: 'bubbleLabels',
        afterDatasetDraw(chart) {
          const { ctx } = chart;
          ctx.save();
          ctx.font = '600 11px "Space Grotesk", sans-serif';
          ctx.fillStyle = '#f2f2f0';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          const meta = chart.getDatasetMeta(0);
          meta.data.forEach((element, i) => {
            const dataPoint = chart.data.datasets[0].data[i];
            const r = element.options.radius || 4;
            ctx.fillText(dataPoint.label, element.x, element.y - r - 8);
          });
          ctx.restore();
        }
      }],
    });

    const sorted = [...stats].sort((a, b) => b.median_comp - a.median_comp);
    makeChart(c2.canvas, {
      type: 'bar',
      data: { labels: sorted.map((s) => s.Language), datasets: [{ data: sorted.map((s) => s.median_comp), backgroundColor: ChartTheme.purple }] },
      options: ChartTheme.baseOptions({
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ChartTheme.fmtUsd(ctx.raw) } } },
        scales: { x: { ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtUsd(v) }, grid: { color: ChartTheme.grid } }, y: { ticks: { color: ChartTheme.text, font: { size: 10 } }, grid: { display: false } } },
      }),
    });
  }

  function corrColor(v) {
    // -1..1 -> diverging scale: teal (negative) through dark gray (zero)
    // to accent violet (positive). Matches the two data colors defined
    // in variables.css.
    const neg = [74, 143, 134];   // --data-2
    const mid = [28, 28, 28];     // --surface-2
    const pos = [138, 63, 252];   // --accent
    const [a, b] = v < 0 ? [neg, mid] : [mid, pos];
    const t = Math.min(Math.abs(v), 1);
    const r = Math.round(a[0] + t * (b[0] - a[0]));
    const g = Math.round(a[1] + t * (b[1] - a[1]));
    const bl = Math.round(a[2] + t * (b[2] - a[2]));
    return `rgb(${r},${g},${bl})`;
  }

  function renderSatisfaction(data) {
    const wrap = el('div');

    const stats = el('div', 'stat-row');
    stats.appendChild(statBox(data.n.toLocaleString(), 'Respondents (n)'));
    stats.appendChild(statBox(data.controlled_r2.toFixed(3), 'Controlled model R²'));
    stats.appendChild(statBox(data.raw_vs_controlled.controlled_coefficient[1].toFixed(2), 'Silos effect (std. coef.)'));
    wrap.appendChild(stats);

    const grid = el('div', 'chart-grid');
    wrap.appendChild(grid);

    const c1card = el('div', 'card full');
    c1card.appendChild(el('div', 'card-title', 'Correlation with job satisfaction'));
    const table = el('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.fontSize = '0.78rem';
    const labels = data.correlation_matrix.labels;
    const matrix = data.correlation_matrix.matrix;
    let thead = '<tr><td></td>' + labels.map((l) => `<td style="padding:8px;color:var(--text-muted);font-family:var(--font-mono);white-space:nowrap;">${l}</td>`).join('') + '</tr>';
    let rows = matrix.map((row, i) => {
      const cells = row.map((v) => `<td class="num" style="padding:10px;text-align:center;background:${corrColor(v)};color:#ffffff;font-weight:600;">${v.toFixed(2)}</td>`).join('');
      return `<tr><td style="padding:8px;color:var(--text-muted);white-space:nowrap;">${labels[i]}</td>${cells}</tr>`;
    }).join('');
    table.innerHTML = thead + rows;
    c1card.appendChild(table);
    grid.appendChild(c1card);

    const c2 = chartCard('Raw correlation vs. controlled for country', null, true);
    grid.appendChild(c2.card);

    panel.innerHTML = '';
    panel.appendChild(wrap);

    makeChart(c2.canvas, {
      type: 'bar',
      data: {
        labels: data.raw_vs_controlled.labels,
        datasets: [
          { label: 'Raw correlation', data: data.raw_vs_controlled.raw_correlation, backgroundColor: ChartTheme.purpleDeep },
          { label: 'Controlled for country', data: data.raw_vs_controlled.controlled_coefficient, backgroundColor: ChartTheme.purple },
        ],
      },
      options: ChartTheme.baseOptions({
        indexAxis: 'y',
        scales: { x: { ticks: { color: ChartTheme.text }, grid: { color: ChartTheme.grid } }, y: { ticks: { color: ChartTheme.text }, grid: { display: false } } },
      }),
    });
  }

  function renderModelInsights(data) {
    const wrap = el('div');

    const stats = el('div', 'stat-row');
    stats.appendChild(statBox(data.metrics.random_forest.r2.toFixed(3), 'Random Forest R²'));
    stats.appendChild(statBox(ChartTheme.fmtUsd(data.metrics.random_forest.mae_usd), 'Mean absolute error'));
    stats.appendChild(statBox(ChartTheme.fmtPct(data.metrics.random_forest.mape), 'Mean % error'));
    wrap.appendChild(stats);

    const grid = el('div', 'chart-grid');
    wrap.appendChild(grid);

    const c1 = chartCard('What actually predicts pay?', 'tall', true);
    grid.appendChild(c1.card);
    const c2 = chartCard("Ridge model error by country (out-of-fold)");
    grid.appendChild(c2.card);
    const c3 = chartCard('Ridge vs. Random Forest');
    grid.appendChild(c3.card);

    panel.innerHTML = '';
    panel.appendChild(wrap);

    const entries = Object.entries(data.feature_importance).sort((a, b) => a[1] - b[1]);
    makeChart(c1.canvas, {
      type: 'bar',
      data: {
        labels: entries.map((e) => e[0]),
        datasets: [{
          data: entries.map((e) => e[1]),
          backgroundColor: entries.map((e) => data.is_language[e[0]] ? ChartTheme.purpleLight : ChartTheme.purple),
        }],
      },
      options: ChartTheme.baseOptions({
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ChartTheme.fmtPct(ctx.raw) } } },
        scales: { x: { ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtPct(v) }, grid: { color: ChartTheme.grid } }, y: { ticks: { color: ChartTheme.text, font: { size: 10 } }, grid: { display: false } } },
      }),
    });

    const mapeEntries = Object.entries(data.mape_by_country).sort((a, b) => a[1] - b[1]);
    makeChart(c2.canvas, {
      type: 'bar',
      data: { labels: mapeEntries.map((e) => e[0]), datasets: [{ data: mapeEntries.map((e) => e[1]), backgroundColor: ChartTheme.purpleLight }] },
      options: ChartTheme.baseOptions({
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ChartTheme.fmtPct(ctx.raw) } } },
        scales: { x: { ticks: { color: ChartTheme.text, callback: (v) => ChartTheme.fmtPct(v) }, grid: { color: ChartTheme.grid } }, y: { ticks: { color: ChartTheme.text }, grid: { display: false } } },
      }),
    });

    makeChart(c3.canvas, {
      type: 'bar',
      data: {
        labels: ['R²', 'MAPE'],
        datasets: [
          { label: 'Ridge', data: [data.metrics.ridge.r2, data.metrics.ridge.mape], backgroundColor: ChartTheme.purpleDeep },
          { label: 'Random Forest', data: [data.metrics.random_forest.r2, data.metrics.random_forest.mape], backgroundColor: ChartTheme.purple },
        ],
      },
      options: ChartTheme.baseOptions({
        scales: { x: { ticks: { color: ChartTheme.text }, grid: { display: false } }, y: { ticks: { color: ChartTheme.text }, grid: { color: ChartTheme.grid } } },
      }),
    });
  }

  const renderers = {
    overview: renderOverview,
    pay_by_country: renderPayByCountry,
    languages: renderLanguages,
    satisfaction: renderSatisfaction,
    model_insights: renderModelInsights,
  };

  async function loadSection(name) {
    destroyCharts();
    panel.innerHTML = '<div class="loading-skeleton"></div>';
    try {
      if (!sectionCache[name]) {
        sectionCache[name] = await Api.get(`/api/dashboard/${name}`);
      }
      renderers[name](sectionCache[name]);
    } catch (err) {
      panel.innerHTML = `<div class="empty-state">Couldn't load this section: ${err.message}</div>`;
    }
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      loadSection(btn.dataset.section);
    });
  });

  loadSection('overview');
})();
