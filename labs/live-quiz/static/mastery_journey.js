/* Anonymous mastery journey progress.
 *
 * There is deliberately no request API in this file.  The only persisted value
 * is a mapping from the six public week IDs to public checkpoint IDs.  No name,
 * student ID, answer, payload, evidence, URL, time, or free text is collected.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "kosen.mastery.journey.v1";
  var WEEK_ID = /^week0[1-6]$/;
  var CHECKPOINT_ID = /^[a-z][a-z0-9-]{0,31}$/;
  var memoryState = {};

  function cleanState(candidate) {
    var out = {};
    if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return out;
    Object.keys(candidate).forEach(function (weekId) {
      if (!WEEK_ID.test(weekId) || !Array.isArray(candidate[weekId])) return;
      out[weekId] = candidate[weekId].filter(function (checkpointId, index, all) {
        return typeof checkpointId === "string" && CHECKPOINT_ID.test(checkpointId) &&
          all.indexOf(checkpointId) === index;
      });
    });
    return out;
  }

  function readState() {
    try {
      memoryState = cleanState(JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}"));
    } catch (_error) {
      memoryState = cleanState(memoryState);
    }
    return memoryState;
  }

  function saveState(state) {
    memoryState = cleanState(state);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(memoryState));
    } catch (_error) {
      /* Storage is optional; controls still work for the current page view. */
    }
  }

  function selectedFor(state, weekId) {
    return new Set(state[weekId] || []);
  }

  function setProgress(progress, earned, maximum) {
    progress.max = maximum;
    progress.value = earned;
    progress.textContent = Math.round(earned / maximum * 100) + "%";
  }

  function setupWeek(root) {
    var weekId = root.dataset.weekId;
    var maximum = Number(root.dataset.weekXp);
    var rank = root.dataset.rank;
    var checkpoints = Array.from(root.querySelectorAll("[data-checkpoint]"));
    var reset = root.querySelector("[data-reset-week]");
    if (!WEEK_ID.test(weekId) || !Number.isFinite(maximum) || maximum <= 0) return;

    function render() {
      var state = readState();
      var selected = selectedFor(state, weekId);
      var earned = 0;

      checkpoints.forEach(function (checkpoint) {
        var id = checkpoint.dataset.checkpointId;
        var xp = Number(checkpoint.dataset.checkpointXp);
        var complete = selected.has(id);
        if (complete && Number.isFinite(xp)) earned += xp;
        checkpoint.classList.toggle("mx-checkpoint--complete", complete);
        var button = checkpoint.querySelector("[data-checkpoint-toggle]");
        button.setAttribute("aria-pressed", complete ? "true" : "false");
        button.querySelector("[data-checkpoint-action]").textContent = complete
          ? "Checkpoint complete — undo"
          : "Mark checkpoint complete";
      });

      root.querySelectorAll("[data-week-progress]").forEach(function (progress) {
        setProgress(progress, earned, maximum);
      });
      root.querySelectorAll("[data-week-progress-text]").forEach(function (label) {
        label.textContent = earned + " of " + maximum + " XP on this device";
      });
      var rankLabel = root.querySelector("[data-current-rank]");
      if (rankLabel) {
        rankLabel.textContent = earned === maximum
          ? "Rank unlocked: " + rank
          : "Rank in progress: " + rank;
      }
    }

    checkpoints.forEach(function (checkpoint) {
      var button = checkpoint.querySelector("[data-checkpoint-toggle]");
      button.addEventListener("click", function () {
        var state = readState();
        var selected = selectedFor(state, weekId);
        var id = checkpoint.dataset.checkpointId;
        if (!CHECKPOINT_ID.test(id)) return;
        if (selected.has(id)) selected.delete(id); else selected.add(id);
        state[weekId] = Array.from(selected);
        saveState(state);
        render();
      });
    });

    if (reset) {
      reset.addEventListener("click", function () {
        var state = readState();
        delete state[weekId];
        saveState(state);
        render();
        var first = root.querySelector("[data-checkpoint-toggle]");
        if (first) first.focus();
      });
    }
    render();
  }

  function setupOverview() {
    var summaries = Array.from(document.querySelectorAll("[data-week-summary]"));
    if (!summaries.length) return;
    var state = readState();
    summaries.forEach(function (summary) {
      var weekId = summary.dataset.weekId;
      var maximum = Number(summary.dataset.weekXp);
      var selected = selectedFor(state, weekId);
      var earned = Array.from(summary.querySelectorAll("[data-summary-checkpoint]"))
        .reduce(function (total, checkpoint) {
          return total + (selected.has(checkpoint.dataset.checkpointId)
            ? Number(checkpoint.dataset.checkpointXp) || 0
            : 0);
        }, 0);
      setProgress(summary.querySelector("[data-week-summary-progress]"), earned, maximum);
      summary.querySelector("[data-week-summary-text]").textContent =
        earned + " of " + maximum + " XP on this device";
      summary.classList.toggle("mx-rank--complete", earned === maximum);
      summary.classList.toggle("mx-rank--active", earned > 0 && earned < maximum);
    });
  }

  var weekRoot = document.querySelector("[data-mastery-journey]");
  if (weekRoot) setupWeek(weekRoot);
  setupOverview();
}());
