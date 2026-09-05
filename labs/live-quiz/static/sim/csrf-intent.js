/* csrf-intent.js — Week 5 simulation.
 *
 * WHAT THIS IS FOR
 * A state-changing POST is neither necessary nor sufficient to call something
 * CSRF. The transferable test is whether attacker-controlled cross-origin
 * content caused the browser to attach a victim's ambient authority, and
 * whether the target accepted the mutation without adequate proof of intent.
 *
 * This model keeps the concepts students often collapse into one separate:
 *   - SameSite asks whether the request is same-site, not same-origin;
 *   - same-origin policy controls whether attacker code can READ a response,
 *     not whether a classic HTML form can SEND a request;
 *   - a synchronizer token is checked by the target, after authentication;
 *   - XSS runs inside the target origin, so it can normally read both a DOM
 *     token and the response. That is XSS-driven action, not CSRF.
 *
 * The request and cookie are symbolic strings only. This file performs no
 * network operation, reads no browser cookie, and stores no learner data. All
 * rendered values go through textContent; no string is parsed as markup.
 */

var CSRFIntentModel = (function () {
  "use strict";

  var ORIGINS = {
    "cross-site": {
      source: "https://attacker.example",
      target: "https://vault.labs.test",
      sameSite: false,
      sameOrigin: false,
      label: "cross-site and cross-origin"
    },
    "same-site": {
      source: "https://promo.labs.test",
      target: "https://vault.labs.test",
      sameSite: true,
      sameOrigin: false,
      label: "same-site but cross-origin"
    },
    "target-xss": {
      source: "https://vault.labs.test",
      target: "https://vault.labs.test",
      sameSite: true,
      sameOrigin: true,
      label: "same-site and same-origin because injected code runs as the target"
    }
  };

  function cookieDecision(state, origin) {
    if (state.session === "signed-out") {
      return {
        sent: false,
        why: "No — the browser has no victim session cookie to attach."
      };
    }
    if (origin.sameOrigin) {
      return {
        sent: true,
        why: "Yes — this is a same-origin target request, so every listed SameSite mode permits the cookie."
      };
    }
    if (origin.sameSite) {
      return {
        sent: true,
        why: "Yes — the hosts differ, but both HTTPS URLs have the schemeful site labs.test. SameSite is not an origin boundary."
      };
    }
    if (state.sameSite === "none") {
      return {
        sent: true,
        why: "Yes — SameSite=None; Secure permits this cookie on the cross-site HTTPS POST."
      };
    }
    if (state.sameSite === "lax") {
      return {
        sent: false,
        why: "No — explicit SameSite=Lax withholds the cookie on this cross-site POST. Its top-level navigation exception is for safe methods such as GET."
      };
    }
    return {
      sent: false,
      why: "No — SameSite=Strict withholds the cookie because the request context is cross-site."
    };
  }

  function intentDecision(state, origin) {
    if (state.defense === "none") {
      return {
        accepted: true,
        why: "PASS WITHOUT PROOF — the endpoint performs no anti-CSRF validation."
      };
    }
    if (state.token === "valid") {
      if (origin.sameOrigin) {
        return {
          accepted: true,
          why: "PASS — the token is valid. Same-origin XSS can normally read a token rendered into the target page and submit it."
        };
      }
      return {
        accepted: true,
        why: "PASS — the supplied token is valid. This assumes a separate token leak or weakness; same-origin policy did not reveal it directly to this origin."
      };
    }
    return {
      accepted: false,
      why: state.token === "wrong"
        ? "FAIL — a token was supplied, but it is not valid for this victim session."
        : "FAIL — the required synchronizer token is missing."
    };
  }

  function classification(state, origin, cookie, intent, mutation) {
    if (state.session === "signed-out") {
      return {
        kind: "unauthenticated-post",
        bad: false,
        badge: "NO VICTIM AUTHORITY",
        title: "Unauthenticated POST — not CSRF",
        why: "The target receives a POST, but there is no victim session to forge. The protected action returns 401 and no victim state changes."
      };
    }
    if (!cookie.sent) {
      return {
        kind: "blocked-samesite",
        bad: false,
        badge: "COOKIE WITHHELD",
        title: "CSRF attempt blocked by SameSite",
        why: "A victim session exists, but the browser does not attach it in this request context. The target sees an unauthenticated POST and returns 401."
      };
    }
    if (!intent.accepted) {
      return {
        kind: origin.sameOrigin ? "blocked-xss-request" : "blocked-csrf-token",
        bad: false,
        badge: "INTENT REJECTED",
        title: origin.sameOrigin
          ? "Same-origin XSS request blocked in this configuration"
          : "CSRF attempt blocked by the token check",
        why: "The session authenticates who the browser is acting for, but the invalid or missing token fails the separate proof-of-intent check. The target returns 403."
      };
    }
    if (origin.sameOrigin) {
      return {
        kind: "xss-driven-action",
        bad: true,
        badge: "XSS AUTHORITY",
        title: "XSS-driven action — not CSRF",
        why: "Attacker code is executing in the target origin. The browser sends the session, the valid token passes, the mutation occurs, and the script can read the response."
      };
    }
    if (mutation) {
      return {
        kind: "true-csrf",
        bad: true,
        badge: "TRUE CSRF",
        title: "Authenticated state change accepted",
        why: "Attacker-controlled cross-origin content made the browser attach victim authority, and the target accepted the mutation. The attacker does not need to read the response."
      };
    }
    return {
      kind: "no-mutation",
      bad: false,
      badge: "NO STATE CHANGE",
      title: "No accepted mutation",
      why: "The simulated target did not accept a state change."
    };
  }

  function evaluate(input) {
    var state = {
      origin: ORIGINS[input.origin] ? input.origin : "cross-site",
      session: input.session === "signed-out" ? "signed-out" : "signed-in",
      sameSite: input.sameSite === "none" || input.sameSite === "lax" ? input.sameSite : "strict",
      defense: input.defense === "none" ? "none" : "token",
      token: input.token === "valid" || input.token === "wrong" ? input.token : "missing"
    };
    var origin = ORIGINS[state.origin];
    var cookie = cookieDecision(state, origin);
    var authenticated = cookie.sent;
    var intent = authenticated
      ? intentDecision(state, origin)
      : {
          accepted: false,
          why: "NOT REACHED — authentication failed first, so there is no victim-authorised request whose intent to validate."
        };
    var mutation = authenticated && intent.accepted;
    var responseReadable = origin.sameOrigin;
    var status = !authenticated ? "401 Unauthorized"
      : (!intent.accepted ? "403 Forbidden" : "200 OK — profile changed");
    var result = classification(state, origin, cookie, intent, mutation);

    return {
      state: state,
      source: origin.source,
      target: origin.target,
      relationship: origin.label,
      sameSiteContext: origin.sameSite,
      sameOriginContext: origin.sameOrigin,
      requestSent: true,
      cookieSent: cookie.sent,
      cookieReason: cookie.why,
      authenticated: authenticated,
      intentEvaluated: authenticated,
      intentAccepted: intent.accepted,
      intentReason: intent.why,
      mutation: mutation,
      responseReadable: responseReadable,
      status: status,
      kind: result.kind,
      bad: result.bad,
      badge: result.badge,
      title: result.title,
      diagnosis: result.why
    };
  }

  return { evaluate: evaluate };
}());

/* Export only for the deterministic Node test. `module` does not exist in the
 * browser document, so the simulation still exposes no runtime capability. */
if (typeof module !== "undefined" && module.exports) {
  module.exports = CSRFIntentModel;
}

(function (model) {
  "use strict";
  if (typeof document === "undefined") return;

  var PRESETS = [
    {
      label: "true CSRF",
      state: { origin: "cross-site", session: "signed-in", sameSite: "none", defense: "none", token: "missing" }
    },
    {
      label: "SameSite blocks it",
      state: { origin: "cross-site", session: "signed-in", sameSite: "lax", defense: "none", token: "missing" }
    },
    {
      label: "token blocks it",
      state: { origin: "cross-site", session: "signed-in", sameSite: "none", defense: "token", token: "missing" }
    },
    {
      label: "signed-out POST",
      state: { origin: "cross-site", session: "signed-out", sameSite: "none", defense: "none", token: "missing" }
    },
    {
      label: "sibling-domain trap",
      state: { origin: "same-site", session: "signed-in", sameSite: "strict", defense: "none", token: "missing" }
    },
    {
      label: "XSS crosses the line",
      state: { origin: "target-xss", session: "signed-in", sameSite: "strict", defense: "token", token: "valid" }
    }
  ];

  var source = document.getElementById("source");
  var sessionState = document.getElementById("session-state");
  var sameSite = document.getElementById("same-site");
  var defense = document.getElementById("csrf-defense");
  var token = document.getElementById("request-token");
  var presets = document.getElementById("presets");
  var summary = document.getElementById("summary");

  function stateFromControls() {
    return {
      origin: source.value,
      session: sessionState.value,
      sameSite: sameSite.value,
      defense: defense.value,
      token: token.value
    };
  }

  function step(id, text, stateClass) {
    var el = document.getElementById(id);
    el.className = "prompt-guard-step" + (stateClass ? " " + stateClass : "");
    document.getElementById(id.replace("step-", "") + "-result").textContent = text;
  }

  function render() {
    var result = model.evaluate(stateFromControls());
    var cookieName = result.cookieSent ? "session=•••• (attached)" : "(session cookie not attached)";
    var tokenField = result.state.defense === "none"
      ? "_csrf=(server does not check one)"
      : "_csrf=" + result.state.token;

    document.getElementById("wire").textContent =
      "Source document: " + result.source + "\n"
      + "Target: POST " + result.target + "/api/profile/email\n"
      + "Content-Type: application/x-www-form-urlencoded\n"
      + "Cookie: " + cookieName + "\n\n"
      + "email=changed%40example.test&" + tokenField + "\n\n"
      + "Target response: " + result.status;

    document.getElementById("relationship").textContent =
      "Boundary check: source and target are " + result.relationship + ".";

    token.disabled = result.state.defense === "none";
    document.getElementById("token-help").textContent = result.state.defense === "none"
      ? "The selected endpoint ignores token input, so the token control is disabled."
      : (result.sameOriginContext
        ? "The model assumes the token is rendered in the target page. Same-origin injected script can normally obtain it."
        : (result.state.token === "valid"
          ? "A cross-origin page cannot read the target token through same-origin policy. Selecting valid models a separate leak or broken token design."
          : "The attacker origin cannot directly read a token rendered by the target because the origins differ."));

    step("step-request",
      "✓ SENT — a browser can emit this form-compatible POST without reading the target first.", "");
    step("step-cookie", (result.cookieSent ? "⚠ " : "✓ ") + result.cookieReason,
      result.cookieSent ? "is-bad" : "is-blocked");
    step("step-auth", result.authenticated
      ? "⚠ AUTHENTICATED — the target resolves the request as the signed-in victim."
      : "✓ UNAUTHENTICATED — the protected target has no victim session to use.",
      result.authenticated ? "is-bad" : "is-blocked");
    step("step-intent", (result.intentAccepted ? "⚠ " : "✓ ") + result.intentReason,
      result.intentAccepted ? "is-bad" : "is-blocked");
    step("step-action", result.mutation
      ? "✗ MUTATED — the target accepts the email change under victim authority."
      : "✓ NOT MUTATED — the protected state remains unchanged (" + result.status + ").",
      result.mutation ? "is-bad" : "is-blocked");
    step("step-read", result.responseReadable
      ? "✗ YES — code runs in the target origin, so same-origin policy permits reading it."
      : "✓ NO — same-origin policy keeps the cross-origin response opaque to attacker code.",
      result.responseReadable ? "is-bad" : "is-blocked");

    summary.className = "iam-evaluation-verdict " + (result.bad ? "is-deny" : "is-allow");
    document.getElementById("summary-badge").textContent = result.bad ? "✗ " + result.badge : "✓ " + result.badge;
    document.getElementById("summary-title").textContent = result.title;
    document.getElementById("summary-detail").textContent = result.diagnosis;

    var diagnosis = document.getElementById("diagnosis");
    diagnosis.className = "verdict " + (result.bad ? "bad" : "ok");
    diagnosis.textContent = result.title;
    document.getElementById("diagnosis-why").textContent = result.diagnosis;
    document.getElementById("response-note").textContent = result.responseReadable
      ? "The response is readable because the attacker code is executing at the exact target origin. That capability change is the XSS/CSRF dividing line in this model."
      : "The response is not readable to the attacker origin — but unreadable does not mean harmless. A cross-origin form can still cause a server-side effect.";
  }

  function applyPreset(preset) {
    source.value = preset.state.origin;
    sessionState.value = preset.state.session;
    sameSite.value = preset.state.sameSite;
    defense.value = preset.state.defense;
    token.value = preset.state.token;
    render();
  }

  PRESETS.forEach(function (preset) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.addEventListener("click", function () { applyPreset(preset); });
    presets.appendChild(button);
  });

  [source, sessionState, sameSite, defense, token].forEach(function (control) {
    control.addEventListener("change", render);
  });

  applyPreset(PRESETS[0]);
}(CSRFIntentModel));
