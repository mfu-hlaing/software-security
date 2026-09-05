'use strict';
(() => {
  const KEY = 'ss-semester-v1';
  const names = ['explain', 'practice', 'defend'];
  let state = {last: 1, done: []};
  let storageAvailable = true;
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && typeof saved === 'object') {
      if (Number.isInteger(saved.last) && saved.last >= 1 && saved.last <= 19) state.last = saved.last;
      if (Array.isArray(saved.done)) state.done = [...new Set(saved.done.filter(x => typeof x === 'string' && /^(?:[1-9]|1[0-9]):(?:explain|practice|defend)$/.test(x)))];
    }
  } catch (_) { storageAvailable = false; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) { storageAvailable = false; } }
  const overview = document.querySelector('[data-journey-index]');
  if (overview) {
    let complete = 0;
    document.querySelectorAll('[data-week]').forEach(card => {
      const n = Number(card.dataset.week);
      const count = names.filter(x => state.done.includes(`${n}:${x}`)).length;
      card.dataset.complete = String(count === 3);
      if (count === 3) complete++;
      card.querySelector('[data-week-status]').textContent = count ? `${count}/3 self-checks · revisit →` : 'Explore week →';
    });
    const resume = document.querySelector('[data-resume]');
    resume.href = `/learn/software-security/journey/week/${state.last}`;
    resume.textContent = `Continue Week ${state.last}`;
    document.querySelector('[data-overview-status]').textContent = `${complete}/19 weeks self-checked on this device. This is not a grade or submitted work.${storageAvailable ? '' : ' Browser storage is unavailable; progress will last only for this page.'}`;
  }
  const page = document.querySelector('[data-journey-week]');
  if (!page) return;
  const n = Number(page.dataset.journeyWeek);
  state.last = n; save();
  const boxes = [...page.querySelectorAll('[data-checkpoint]')];
  function render() {
    boxes.forEach(box => { box.checked = state.done.includes(`${n}:${box.dataset.checkpoint}`); });
    const count = boxes.filter(box => box.checked).length;
    page.querySelector('[data-progress-status]').textContent = `${count}/3 self-checks completed.${storageAvailable ? ' Saved only on this device.' : ' Browser storage unavailable; progress lasts only for this page.'}`;
  }
  boxes.forEach(box => box.addEventListener('change', () => {
    const key = `${n}:${box.dataset.checkpoint}`;
    state.done = state.done.filter(x => x !== key);
    if (box.checked) state.done.push(key);
    save(); render();
  }));
  page.querySelector('[data-reset-week]').addEventListener('click', () => {
    state.done = state.done.filter(x => !x.startsWith(`${n}:`)); save(); render();
  });
  page.querySelectorAll('[data-question]').forEach(question => {
    question.querySelector('[data-check-answer]').addEventListener('click', () => {
      const chosen = question.querySelector('input:checked');
      const feedback = question.querySelector('.sj-feedback');
      if (!chosen) { feedback.textContent = 'Choose an answer first, or open the explanation to study it.'; return; }
      feedback.textContent = Number(chosen.value) === Number(question.dataset.answer) ? 'Correct. Explain why the other choices fail.' : 'Revisit the mechanism, then try again. The explanation below shows the reasoning.';
      question.querySelector('details').open = true;
    });
  });
  page.querySelector('[data-reset-quiz]').addEventListener('click', () => {
    page.querySelectorAll('.sj-question input').forEach(input => { input.checked = false; });
    page.querySelectorAll('.sj-feedback').forEach(el => { el.textContent = ''; });
    page.querySelectorAll('.sj-rationale').forEach(el => { el.open = false; });
  });
  render();
})();
