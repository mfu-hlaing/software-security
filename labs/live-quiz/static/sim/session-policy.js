/* session-policy.js — Week 6 authentication and authorization simulation.
 *
 * Two concepts are deliberately separated:
 *
 *   1. A session is a server-side lifecycle: rotate when privilege changes,
 *      expire on both idle and absolute clocks, and revoke on logout.
 *   2. An authenticated subject still needs an authorization decision for the
 *      exact subject/action/object tuple. No matching allow means deny.
 *
 * Readable session labels make state transitions visible on a projector. They
 * are fixed teaching labels, not random values and not a recipe for real token
 * construction. All state remains in memory in this sandboxed page.
 */
(function () {
  "use strict";

  var IDLE_LIMIT = 4;
  var ABSOLUTE_LIMIT = 10;

  function createSessionModel(rotateOnLogin) {
    var state;

    function setResult(tone, headline, detail) {
      state.result = { tone: tone, headline: headline, detail: detail };
    }

    function addTrace(message) {
      state.trace.push("m" + state.clock + " · " + message);
      if (state.trace.length > 10) state.trace.shift();
    }

    function invalidate(id, reason) {
      if (id) state.invalid[id] = reason;
    }

    function expireIfNeeded() {
      if (!state.active || !state.active.authenticated) return false;
      var absoluteAge = state.clock - state.active.issuedAt;
      var idleAge = state.clock - state.active.lastActivity;
      var reason = null;

      /* Absolute wins when both boundaries are reached on the same request: it
         cannot be extended by activity, which is the idea this branch teaches. */
      if (absoluteAge >= ABSOLUTE_LIMIT) {
        reason = "absolute lifetime reached";
      } else if (idleAge >= IDLE_LIMIT) {
        reason = "idle timeout reached";
      }

      if (!reason) return false;
      var expiredId = state.active.id;
      invalidate(expiredId, reason);
      state.active = null;
      addTrace(expiredId + " expired: " + reason);
      setResult("ok", "Expired before reuse", reason
        + ". The server removed the record, so the browser-held label no longer authenticates.");
      return true;
    }

    function reset(rotation) {
      state = {
        clock: 0,
        rotation: rotation !== false,
        active: {
          id: "toy-sid-pre-A1",
          authenticated: false,
          subject: "anonymous",
          issuedAt: null,
          lastActivity: 0
        },
        browserId: "toy-sid-pre-A1",
        savedId: null,
        invalid: Object.create(null),
        nextAuthId: 1,
        trace: [],
        result: null
      };
      addTrace("anonymous pre-login record created");
      setResult("neutral", "Ready", "Save the pre-login label, choose a rotation policy, then log in.");
    }

    function setRotation(enabled) {
      state.rotation = enabled;
      setResult("neutral", enabled ? "Rotation enabled" : "Rotation disabled",
        "This choice applies at the next login transition; it does not rewrite an existing session.");
    }

    function saveLabel() {
      if (!state.browserId) {
        setResult("bad", "Nothing to save", "This browser currently holds no session label.");
        return;
      }
      state.savedId = state.browserId;
      addTrace("a second tab saved label " + state.savedId);
      setResult("neutral", "Pre-login label saved", "The second tab can present this same toy label later.");
    }

    function login() {
      if (!state.active) {
        setResult("bad", "Login cannot continue", "Reset first to create a fresh pre-login record.");
        return;
      }
      if (state.active.authenticated) {
        setResult("neutral", "Already logged in", "Reset to replay the login transition.");
        return;
      }

      var oldId = state.active.id;
      var newId = oldId;
      if (state.rotation) {
        newId = "toy-sid-auth-B" + state.nextAuthId;
        state.nextAuthId += 1;
        invalidate(oldId, "replaced during login rotation");
      }
      state.active = {
        id: newId,
        authenticated: true,
        subject: "learner-alpha",
        issuedAt: state.clock,
        lastActivity: state.clock
      };
      state.browserId = newId;
      addTrace("login accepted; " + oldId + (oldId === newId
        ? " was reused"
        : " rotated to " + newId));

      if (oldId === newId) {
        setResult("bad", "Login reused the known label", "Identity changed from anonymous to Learner Alpha, but the identifier did not. A saved copy now names the authenticated record.");
      } else {
        setResult("ok", "Login rotated the label", "The anonymous label was invalidated before the authenticated record was created.");
      }
    }

    function advance(minutes) {
      state.clock += minutes;
      addTrace("clock advanced by " + minutes + (minutes === 1 ? " minute" : " minutes"));
      if (!expireIfNeeded()) {
        setResult("neutral", "Time advanced", "The server checks both clocks before accepting the next use.");
      }
    }

    function touch() {
      if (expireIfNeeded()) return;
      if (!state.active || !state.active.authenticated) {
        setResult("bad", "Protected request rejected", "No live authenticated server record matches this browser state.");
        addTrace("protected request rejected");
        return;
      }
      state.active.lastActivity = state.clock;
      addTrace("protected request accepted; idle clock refreshed");
      setResult("ok", "Protected request accepted", "Idle age returned to zero. Absolute age did not: activity cannot extend the hard lifetime.");
    }

    function replaySaved() {
      expireIfNeeded();
      if (!state.savedId) {
        setResult("neutral", "No saved label", "Use “Save pre-login label” before trying the second tab.");
        return;
      }
      if (state.active && state.active.authenticated && state.savedId === state.active.id) {
        state.active.lastActivity = state.clock;
        addTrace("saved label matched the authenticated record");
        setResult("bad", "Saved label accepted", "This is session fixation: the login upgraded an identifier another tab already possessed.");
        return;
      }
      var reason = state.invalid[state.savedId] || "no matching live record";
      addTrace("saved label rejected: " + reason);
      setResult("ok", "Saved label rejected", reason + ". Possessing an old label is not enough to recover a live identity.");
    }

    function logout() {
      expireIfNeeded();
      if (!state.active || !state.active.authenticated) {
        setResult("neutral", "No authenticated session", "There is no live login to revoke.");
        return;
      }
      var oldId = state.active.id;
      invalidate(oldId, "revoked by logout");
      state.active = null;
      state.browserId = null;
      addTrace(oldId + " revoked by logout");
      setResult("ok", "Logout revoked the server record", "A copied browser label now resolves to an invalid record, not an authenticated identity.");
    }

    function snapshot() {
      return {
        clock: state.clock,
        rotation: state.rotation,
        active: state.active ? {
          id: state.active.id,
          authenticated: state.active.authenticated,
          subject: state.active.subject,
          issuedAt: state.active.issuedAt,
          lastActivity: state.active.lastActivity
        } : null,
        browserId: state.browserId,
        browserReason: state.browserId ? state.invalid[state.browserId] || null : null,
        savedId: state.savedId,
        savedReason: state.savedId ? state.invalid[state.savedId] || null : null,
        trace: state.trace.slice(),
        result: {
          tone: state.result.tone,
          headline: state.result.headline,
          detail: state.result.detail
        }
      };
    }

    reset(rotateOnLogin);
    return {
      reset: reset,
      setRotation: setRotation,
      saveLabel: saveLabel,
      login: login,
      advance: advance,
      touch: touch,
      replaySaved: replaySaved,
      logout: logout,
      snapshot: snapshot
    };
  }

  var SUBJECTS = {
    anonymous: { label: "Anonymous visitor", authenticated: false, role: "anonymous" },
    "learner-alpha": { label: "Learner Alpha", authenticated: true, role: "learner" },
    "learner-beta": { label: "Learner Beta", authenticated: true, role: "learner" },
    "course-admin": { label: "Course administrator", authenticated: true, role: "admin" }
  };

  var OBJECTS = {
    "public-guide": { label: "Public course guide", kind: "public", owner: null },
    "alpha-note": { label: "Alpha's private note", kind: "note", owner: "learner-alpha" },
    "beta-note": { label: "Beta's private note", kind: "note", owner: "learner-beta" },
    "class-roster": { label: "Restricted class roster", kind: "roster", owner: null }
  };

  function secureRule(subjectKey, action, objectKey) {
    var subject = SUBJECTS[subjectKey];
    var object = OBJECTS[objectKey];
    if (!subject || !object) return null;

    if (object.kind === "public" && action === "view") {
      return "Public-read rule: anyone may view the course guide.";
    }
    if (object.kind === "note" && subject.authenticated
        && object.owner === subjectKey
        && (action === "view" || action === "edit" || action === "delete")) {
      return "Owner rule: a learner may view, edit or delete their own note.";
    }
    if (object.kind === "note" && subject.role === "admin"
        && (action === "view" || action === "delete")) {
      return "Administrator oversight rule: an administrator may view or delete a note, but not edit its content.";
    }
    if (object.kind === "roster" && subject.role === "admin" && action === "view") {
      return "Roster rule: an administrator may view the restricted roster.";
    }
    return null;
  }

  function evaluateAuthorization(subjectKey, action, objectKey, mode) {
    var subject = SUBJECTS[subjectKey] || SUBJECTS.anonymous;
    var object = OBJECTS[objectKey] || { label: "Unknown object", kind: "unknown", owner: null };
    var identityStep = subject.authenticated
      ? "Valid toy identity resolved for " + subject.label + "."
      : "No authenticated identity was presented; the subject is anonymous.";

    if (mode === "identity-only") {
      var identityAllows = subject.authenticated;
      return {
        authenticated: subject.authenticated,
        allowed: identityAllows,
        flawed: true,
        summary: identityAllows ? "ALLOW — identity-only gate" : "DENY — no valid identity",
        explanation: identityAllows
          ? "The implementation stopped after authentication and never checked the action or object. A valid identity was mistaken for universal permission."
          : "This flawed gate rejects an anonymous subject, but still over-grants every signed-in subject.",
        policy: "IF identity is valid: ALLOW every action on every object\nELSE: DENY",
        steps: [
          { state: subject.authenticated ? "pass" : "stop", title: "Resolve identity", detail: identityStep },
          { state: "skip", title: "Check subject + action + object", detail: "Skipped by this flawed implementation." },
          { state: identityAllows ? "stop" : "pass", title: "Return decision", detail: identityAllows ? "Allowed without an authorization rule." : "Denied because authentication failed." }
        ]
      };
    }

    var rule = secureRule(subjectKey, action, objectKey);
    var allowed = Boolean(rule);
    var tuple = subject.label + " → " + action + " → " + object.label;
    return {
      authenticated: subject.authenticated,
      allowed: allowed,
      flawed: false,
      summary: allowed ? "ALLOW — exact rule matched" : "DENY — default deny",
      explanation: allowed
        ? rule + " The decision applies only to this subject/action/object tuple."
        : "No allow rule matches “" + tuple + "”. A valid identity does not change the fallback: unmatched requests are denied.",
      policy: "ALLOW anyone to view the public guide\nALLOW an owner to view/edit/delete their own note\nALLOW an administrator to view/delete any note\nALLOW an administrator to view the roster\nDENY every unmatched request",
      steps: [
        { state: "pass", title: "Build subject context", detail: identityStep },
        { state: allowed ? "pass" : "stop", title: "Match subject + action + object", detail: allowed ? rule : "No exact allow rule matched." },
        { state: allowed ? "pass" : "stop", title: "Apply fallback", detail: allowed ? "A named allow decides this request." : "Default deny decides this request." }
      ]
    };
  }

  /* Pure model exports make the state machine testable with Node. This branch
     returns before any browser object is read and has no effect in the page. */
  if (typeof module === "object" && module.exports) {
    module.exports = {
      createSessionModel: createSessionModel,
      evaluateAuthorization: evaluateAuthorization
    };
    return;
  }

  function el(id) {
    return document.getElementById(id);
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function addButton(container, label, action) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", action);
    container.appendChild(button);
  }

  var session = createSessionModel(true);
  var rotationOn = el("rotation-on");
  var rotationOff = el("rotation-off");
  var saveButton = el("save-id");
  var loginButton = el("login");
  var logoutButton = el("logout");
  var replayButton = el("replay-id");
  var sessionState = el("session-state");
  var sessionVerdict = el("session-verdict");
  var sessionExplanation = el("session-explanation");
  var sessionTrace = el("session-trace");

  function renderSession() {
    var snap = session.snapshot();
    var active = snap.active;
    var lines = [
      "Clock: minute " + snap.clock,
      "Browser-held label: " + (snap.browserId || "cleared"),
      "Server record: " + (active
        ? active.authenticated ? "Learner Alpha (authenticated)" : "anonymous (pre-login)"
        : "no live record"),
      "Second-tab label: " + (snap.savedId || "not saved"),
      "Login rotation: " + (snap.rotation ? "ON" : "OFF")
    ];
    if (snap.browserReason) lines.push("Browser label status: invalid — " + snap.browserReason);
    if (active && active.authenticated) {
      lines.push("Idle age: " + (snap.clock - active.lastActivity) + " / " + IDLE_LIMIT + " minutes");
      lines.push("Absolute age: " + (snap.clock - active.issuedAt) + " / " + ABSOLUTE_LIMIT + " minutes");
    }
    if (snap.savedReason) lines.push("Saved label status: invalid — " + snap.savedReason);
    sessionState.textContent = lines.join("\n");
    sessionTrace.textContent = snap.trace.join("\n");
    sessionVerdict.className = "verdict" + (snap.result.tone === "bad"
      ? " bad" : snap.result.tone === "ok" ? " ok" : "");
    sessionVerdict.textContent = snap.result.headline;
    sessionExplanation.textContent = snap.result.detail;

    rotationOn.checked = snap.rotation;
    rotationOff.checked = !snap.rotation;
    saveButton.disabled = !snap.browserId;
    loginButton.disabled = !active || active.authenticated;
    logoutButton.disabled = !active || !active.authenticated;
    replayButton.disabled = !snap.savedId;
  }

  function runSession(action) {
    action();
    renderSession();
  }

  rotationOn.addEventListener("change", function () {
    if (rotationOn.checked) runSession(function () { session.setRotation(true); });
  });
  rotationOff.addEventListener("change", function () {
    if (rotationOff.checked) runSession(function () { session.setRotation(false); });
  });
  saveButton.addEventListener("click", function () { runSession(session.saveLabel); });
  loginButton.addEventListener("click", function () { runSession(session.login); });
  el("advance-one").addEventListener("click", function () {
    runSession(function () { session.advance(1); });
  });
  el("advance-four").addEventListener("click", function () {
    runSession(function () { session.advance(4); });
  });
  el("use-session").addEventListener("click", function () { runSession(session.touch); });
  replayButton.addEventListener("click", function () { runSession(session.replaySaved); });
  logoutButton.addEventListener("click", function () { runSession(session.logout); });
  el("reset-session").addEventListener("click", function () {
    runSession(function () { session.reset(rotationOn.checked); });
  });

  addButton(el("session-scenarios"), "Fixation when login reuses an ID", function () {
    session.reset(false);
    session.saveLabel();
    session.login();
    session.replaySaved();
    renderSession();
  });
  addButton(el("session-scenarios"), "Rotation blocks the saved ID", function () {
    session.reset(true);
    session.saveLabel();
    session.login();
    session.replaySaved();
    renderSession();
  });
  addButton(el("session-scenarios"), "Idle expiry", function () {
    session.reset(true);
    session.login();
    session.advance(4);
    renderSession();
  });
  addButton(el("session-scenarios"), "Absolute expiry despite activity", function () {
    session.reset(true);
    session.login();
    session.advance(3);
    session.touch();
    session.advance(3);
    session.touch();
    session.advance(3);
    session.touch();
    session.advance(1);
    renderSession();
  });

  var subjectSelect = el("policy-subject");
  var actionSelect = el("policy-action");
  var objectSelect = el("policy-object");
  var rulesMode = el("policy-rules");
  var identityMode = el("policy-identity");
  var policyText = el("policy-text");
  var policyVerdict = el("policy-verdict");
  var policyBadge = el("policy-badge");
  var policySummary = el("policy-summary");
  var policyExplanation = el("policy-explanation");
  var policySteps = el("policy-steps");

  function renderPolicySteps(steps) {
    clear(policySteps);
    steps.forEach(function (step, index) {
      var row = document.createElement("div");
      row.className = "iam-evaluation-step is-" + step.state;
      var number = document.createElement("span");
      number.className = "iam-evaluation-num";
      number.textContent = String(index + 1);
      var body = document.createElement("div");
      body.className = "iam-evaluation-body";
      var title = document.createElement("p");
      title.className = "iam-evaluation-q";
      title.textContent = step.title;
      var detail = document.createElement("p");
      detail.className = "iam-evaluation-d";
      detail.textContent = step.detail;
      body.appendChild(title);
      body.appendChild(detail);
      row.appendChild(number);
      row.appendChild(body);
      policySteps.appendChild(row);
    });
  }

  function renderPolicy() {
    var mode = identityMode.checked ? "identity-only" : "rules";
    var decision = evaluateAuthorization(subjectSelect.value, actionSelect.value,
      objectSelect.value, mode);
    policyVerdict.className = "iam-evaluation-verdict "
      + (decision.allowed ? "is-allow" : "is-deny");
    policyBadge.textContent = decision.allowed ? "ALLOW" : "DENY";
    policySummary.textContent = decision.summary;
    policyExplanation.textContent = decision.explanation;
    policyText.textContent = decision.policy;
    renderPolicySteps(decision.steps);
  }

  function selectPolicyPreset(subject, action, object, mode) {
    subjectSelect.value = subject;
    actionSelect.value = action;
    objectSelect.value = object;
    rulesMode.checked = mode === "rules";
    identityMode.checked = mode === "identity-only";
    renderPolicy();
  }

  addButton(el("policy-scenarios"), "Signed in, still denied", function () {
    selectPolicyPreset("learner-alpha", "edit", "beta-note", "rules");
  });
  addButton(el("policy-scenarios"), "Owner edits own note", function () {
    selectPolicyPreset("learner-alpha", "edit", "alpha-note", "rules");
  });
  addButton(el("policy-scenarios"), "Administrator reviews a note", function () {
    selectPolicyPreset("course-admin", "view", "beta-note", "rules");
  });
  addButton(el("policy-scenarios"), "Administrator cannot rewrite it", function () {
    selectPolicyPreset("course-admin", "edit", "beta-note", "rules");
  });
  addButton(el("policy-scenarios"), "Public read without login", function () {
    selectPolicyPreset("anonymous", "view", "public-guide", "rules");
  });
  addButton(el("policy-scenarios"), "Identity-only over-grant", function () {
    selectPolicyPreset("learner-beta", "delete", "alpha-note", "identity-only");
  });

  [subjectSelect, actionSelect, objectSelect, rulesMode, identityMode].forEach(function (control) {
    control.addEventListener("change", renderPolicy);
  });

  renderSession();
  renderPolicy();
})();
