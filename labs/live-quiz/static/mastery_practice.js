/* Anonymous mastery practice: no requests, no identity, no server-side state. */
(function () {
  "use strict";

  function cleanSaved(candidate, renderedQuestions) {
    var clean = {};
    if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return clean;

    renderedQuestions.forEach(function (question) {
      var id = question.dataset.questionId;
      var value = candidate[id];
      var optionCount = question.querySelectorAll("[data-option]").length;
      if (Object.prototype.hasOwnProperty.call(candidate, id) &&
          Number.isInteger(value) && value >= 0 && value < optionCount) {
        clean[id] = value;
      }
    });
    return clean;
  }

  /* A pure export keeps the storage boundary regression-testable in Node. The
     browser never has CommonJS `module`, so this does not add a page global. */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = {cleanSaved: cleanSaved};
    return;
  }

  var root = document.querySelector("[data-practice]");
  if (!root) return;

  var questions = Array.from(root.querySelectorAll("[data-question]"));
  var score = root.querySelector("[data-score]");
  var scoreMessage = root.querySelector("[data-score-message]");
  var finish = root.querySelector("[data-finish]");
  var finishMessage = root.querySelector("[data-finish-message]");
  var reset = root.querySelector("[data-reset]");
  var storageKey = "kosen.mastery.practice.v1." + root.dataset.bankId;
  var selections = {};

  function readSaved() {
    try {
      var parsed = JSON.parse(window.localStorage.getItem(storageKey) || "{}");
      return cleanSaved(parsed, questions);
    } catch (_error) {
      return {};
    }
  }

  function save() {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(selections));
    } catch (_error) {
      /* Storage is optional; the exercise still works for this page view. */
    }
  }

  function requiredCorrect() {
    var threshold = Number(root.dataset.threshold);
    if (!Number.isFinite(threshold) || threshold <= 0) return questions.length;
    if (threshold <= 1) return Math.ceil(questions.length * threshold);
    if (threshold <= 100) return Math.ceil(questions.length * threshold / 100);
    return questions.length;
  }

  function totals() {
    var answered = Object.keys(selections).length;
    var correct = questions.reduce(function (count, question) {
      var selected = selections[question.dataset.questionId];
      return count + (selected === Number(question.dataset.correctIndex) ? 1 : 0);
    }, 0);
    return {answered: answered, correct: correct};
  }

  function renderScore() {
    var result = totals();
    score.textContent = result.answered + " of " + questions.length +
      " answered · " + result.correct + " correct";

    if (result.answered < questions.length) {
      var remaining = questions.length - result.answered;
      scoreMessage.textContent = remaining + " question" +
        (remaining === 1 ? "" : "s") + " left. Explain your choice before tapping.";
      finish.hidden = true;
      return;
    }

    var target = requiredCorrect();
    var met = result.correct >= target;
    scoreMessage.textContent = met
      ? "Target reached. Revisit any missed rationale before moving on."
      : "Good retrieval attempt. Review the missed rationales and reset for another pass.";
    finishMessage.textContent = "You answered " + result.correct + " of " +
      questions.length + " correctly. The suggested mastery target is " + target +
      ", but this check is private and ungraded.";
    finish.hidden = false;
  }

  function choose(question, selectedIndex, shouldSave) {
    var id = question.dataset.questionId;
    var buttons = Array.from(question.querySelectorAll("[data-option]"));
    if (!Number.isInteger(selectedIndex) || selectedIndex < 0 || selectedIndex >= buttons.length) return;
    if (Object.prototype.hasOwnProperty.call(selections, id)) return;

    var correctIndex = Number(question.dataset.correctIndex);
    var selected = buttons[selectedIndex];
    selections[id] = selectedIndex;
    question.dataset.answered = "true";

    buttons.forEach(function (button, index) {
      button.disabled = true;
      button.setAttribute("aria-pressed", index === selectedIndex ? "true" : "false");
      if (index === correctIndex) button.classList.add("mx-option--correct");
    });
    selected.classList.add("mx-option--selected");
    if (selectedIndex !== correctIndex) selected.classList.add("mx-option--wrong");

    var feedback = question.querySelector("[data-feedback]");
    var rationale = selected.dataset.rationale.replace(/^Correct:\s*/i, "");
    feedback.textContent = (selectedIndex === correctIndex ? "Correct. " : "Not quite. ") +
      rationale;
    feedback.classList.toggle("mx-feedback--correct", selectedIndex === correctIndex);
    feedback.classList.toggle("mx-feedback--wrong", selectedIndex !== correctIndex);
    feedback.hidden = false;
    question.querySelector("[data-explanation]").hidden = false;

    if (shouldSave) save();
    renderScore();
  }

  questions.forEach(function (question) {
    question.querySelectorAll("[data-option]").forEach(function (button) {
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () {
        choose(question, Number(button.dataset.optionIndex), true);
      });
    });
  });

  reset.addEventListener("click", function () {
    selections = {};
    try {
      window.localStorage.removeItem(storageKey);
    } catch (_error) {
      /* Storage is optional. */
    }
    questions.forEach(function (question) {
      delete question.dataset.answered;
      question.querySelectorAll("[data-option]").forEach(function (button) {
        button.disabled = false;
        button.setAttribute("aria-pressed", "false");
        button.classList.remove("mx-option--selected", "mx-option--correct", "mx-option--wrong");
      });
      var feedback = question.querySelector("[data-feedback]");
      feedback.hidden = true;
      feedback.classList.remove("mx-feedback--correct", "mx-feedback--wrong");
      question.querySelector("[data-explanation]").hidden = true;
    });
    renderScore();
    questions[0].querySelector("[data-option]").focus();
  });

  var saved = readSaved();
  questions.forEach(function (question) {
    var value = saved[question.dataset.questionId];
    if (Number.isInteger(value)) choose(question, value, false);
  });
  renderScore();
}());
