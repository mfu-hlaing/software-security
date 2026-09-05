"""Contracts for the Week 5 CSRF/request-intent browser simulation."""

import json
import os
import subprocess

import content as C
from app import app as flask_app


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(HERE, "static", "sim", "csrf-intent.js")


def _evaluate(cases):
    program = (
        "const model=require(" + json.dumps(JS) + ");"
        "const cases=" + json.dumps(cases) + ";"
        "process.stdout.write(JSON.stringify(cases.map(model.evaluate)));"
    )
    result = subprocess.run(
        ["node", "-e", program], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def test_sim_is_registered_to_week_five_and_route_is_hardened():
    assert "csrf-intent" in C.SIMS
    assert C.SIM_SOURCE["csrf-intent"] == (
        "software-security", "week05-xss-client-side"
    )
    flask_app.config["TESTING"] = True
    response = flask_app.test_client().get("/sim/csrf-intent")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "failure to prove request intent" in body
    assert "Unauthenticated POST" in body
    assert "/static/sim/csrf-intent.js?v=" in body
    assert body.count("<h1") == 1
    assert body.count("<h2") == 5
    assert "<h3" not in body
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "script-src 'self'" in csp
    assert "unsafe-inline" not in csp and "unsafe-eval" not in csp


def test_sim_has_no_network_cookie_or_html_execution_capability():
    source = open(JS, encoding="utf-8").read()
    for forbidden in (
        "fetch(", "XMLHttpRequest", "WebSocket", "EventSource",
        "sendBeacon", "document.cookie", "localStorage", "sessionStorage",
        "innerHTML", "insertAdjacentHTML", "document.write", "eval(",
        "new Function(",
    ):
        assert forbidden not in source
    assert ".textContent" in source


def test_true_csrf_requires_ambient_victim_authority_and_accepted_mutation():
    true_csrf, logged_out = _evaluate([
        {
            "origin": "cross-site", "session": "signed-in",
            "sameSite": "none", "defense": "none", "token": "missing",
        },
        {
            "origin": "cross-site", "session": "signed-out",
            "sameSite": "none", "defense": "none", "token": "missing",
        },
    ])
    assert true_csrf["kind"] == "true-csrf"
    assert true_csrf["cookieSent"] and true_csrf["authenticated"]
    assert true_csrf["mutation"] and not true_csrf["responseReadable"]

    assert logged_out["kind"] == "unauthenticated-post"
    assert logged_out["requestSent"]
    assert not logged_out["authenticated"] and not logged_out["mutation"]
    assert not logged_out["intentEvaluated"]
    assert logged_out["status"] == "401 Unauthorized"


def test_samesite_and_token_are_independent_defense_layers():
    lax, token_block = _evaluate([
        {
            "origin": "cross-site", "session": "signed-in",
            "sameSite": "lax", "defense": "none", "token": "missing",
        },
        {
            "origin": "cross-site", "session": "signed-in",
            "sameSite": "none", "defense": "token", "token": "wrong",
        },
    ])
    assert lax["kind"] == "blocked-samesite"
    assert not lax["cookieSent"] and not lax["mutation"]
    assert token_block["kind"] == "blocked-csrf-token"
    assert token_block["cookieSent"] and token_block["authenticated"]
    assert not token_block["intentAccepted"] and not token_block["mutation"]
    assert token_block["status"] == "403 Forbidden"


def test_site_is_not_origin_and_xss_is_not_csrf():
    sibling, xss = _evaluate([
        {
            "origin": "same-site", "session": "signed-in",
            "sameSite": "strict", "defense": "none", "token": "missing",
        },
        {
            "origin": "target-xss", "session": "signed-in",
            "sameSite": "strict", "defense": "token", "token": "valid",
        },
    ])
    assert sibling["sameSiteContext"] and not sibling["sameOriginContext"]
    assert sibling["cookieSent"] and sibling["kind"] == "true-csrf"
    assert not sibling["responseReadable"], "same-site does not bypass SOP"

    assert xss["sameOriginContext"] and xss["cookieSent"]
    assert xss["intentAccepted"] and xss["mutation"]
    assert xss["responseReadable"]
    assert xss["kind"] == "xss-driven-action"
