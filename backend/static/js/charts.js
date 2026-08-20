
const ChartTheme = {
  accent: '#8a3ffc',
  accentSoft: '#b28cf0',
  purple: '#8a3ffc',
  purpleLight: '#b28cf0',
  purpleDeep: '#5c22b8',
  data2: '#4a8f86',
  data2Soft: '#8fb3ae',
  text: '#a8a8a3',
  grid: 'rgba(255,255,255,0.06)',
  palette: ['#8a3ffc', '#4a8f86', '#b28cf0', '#8fb3ae', '#5c22b8', '#2f5f58', '#d3c0f5', '#c2d6d3'],

  baseOptions(overrides = {}) {
    return Object.assign({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: this.text, font: { family: 'Space Grotesk', size: 11 } },
        },
        tooltip: {
          backgroundColor: '#161616',
          borderColor: '#2e2e2e',
          borderWidth: 1,
          titleColor: '#f2f2f0',
          bodyColor: '#a8a8a3',
          padding: 10,
          titleFont: { family: 'Space Grotesk' },
          bodyFont: { family: 'JetBrains Mono' },
        },
      },
      scales: {
        x: {
          ticks: { color: this.text, font: { family: 'Space Grotesk', size: 10 } },
          grid: { color: this.grid },
        },
        y: {
          ticks: { color: this.text, font: { family: 'JetBrains Mono', size: 10 } },
          grid: { color: this.grid },
        },
      },
    }, overrides);
  },

  fmtUsd(v) {
    return '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 });
  },

  fmtPct(v) {
    return (v * 100).toFixed(1) + '%';
  },
};
