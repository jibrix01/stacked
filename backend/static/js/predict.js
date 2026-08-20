(function () {
  const yearsInput = document.getElementById('years');
  const yearsValue = document.getElementById('years-value');
  const countrySelect = document.getElementById('country');
  const edLevelSelect = document.getElementById('ed-level');
  const remoteSelect = document.getElementById('remote-work');
  const chipGroup = document.getElementById('language-chips');
  const form = document.getElementById('predict-form');
  const predictBtn = document.getElementById('predict-btn');

  const resultEmpty = document.getElementById('result-empty');
  const resultContent = document.getElementById('result-content');
  const resultFigure = document.getElementById('result-figure');
  const resultRange = document.getElementById('result-range');
  const metaR2 = document.getElementById('meta-r2');
  const metaMape = document.getElementById('meta-mape');

  let selectedLanguages = new Set();

  function populateSelect(select, values, selected) {
    select.innerHTML = '';
    values.forEach((v) => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      if (v === selected) opt.selected = true;
      select.appendChild(opt);
    });
  }

  function renderChips(languages) {
    chipGroup.innerHTML = '';
    languages.forEach((lang) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip';
      chip.textContent = lang;
      chip.addEventListener('click', () => {
        if (selectedLanguages.has(lang)) {
          selectedLanguages.delete(lang);
          chip.classList.remove('selected');
        } else {
          selectedLanguages.add(lang);
          chip.classList.add('selected');
        }
      });
      chipGroup.appendChild(chip);
    });
  }

  async function init() {
    yearsInput.addEventListener('input', () => {
      yearsValue.textContent = yearsInput.value;
    });

    try {
      const { options, defaults } = await Api.get('/api/predict/options');
      populateSelect(countrySelect, options.countries, defaults.Country_Grouped);
      populateSelect(edLevelSelect, options.ed_levels, defaults.EdLevel);
      populateSelect(remoteSelect, options.remote_work, defaults.RemoteWork);
      renderChips(options.languages);
      yearsInput.value = defaults.YearsCodePro_num;
      yearsValue.textContent = defaults.YearsCodePro_num;
    } catch (err) {
      resultEmpty.textContent = 'Could not load the model options. Is the backend running?';
    }
  }

  async function runPrediction(e) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (predictBtn.disabled) return false;
    predictBtn.disabled = true;
    predictBtn.textContent = 'Estimating...';

    try {
      const payload = {
        years_experience: parseFloat(yearsInput.value),
        country: countrySelect.value,
        ed_level: edLevelSelect.value,
        remote_work: remoteSelect.value,
        languages: Array.from(selectedLanguages),
      };
      const result = await Api.postJSON('/api/predict', payload);

      resultEmpty.style.display = 'none';
      resultContent.style.display = 'block';
      resultFigure.textContent = ChartTheme.fmtUsd(result.predicted_salary_usd);
      resultRange.textContent = `${ChartTheme.fmtUsd(result.range_low_usd)} to ${ChartTheme.fmtUsd(result.range_high_usd)} likely range`;
      metaR2.textContent = result.model_r2.toFixed(2);
      metaMape.textContent = ChartTheme.fmtPct(result.model_mape);
    } catch (err) {
      resultEmpty.style.display = 'block';
      resultContent.style.display = 'none';
      resultEmpty.textContent = 'Something went wrong: ' + err.message;
    } finally {
      predictBtn.disabled = false;
      predictBtn.textContent = 'Estimate salary';
    }
    return false;
  }

  form.addEventListener('submit', runPrediction);
  predictBtn.addEventListener('click', runPrediction);

  init();
})();
