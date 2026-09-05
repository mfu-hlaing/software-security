"""Contracts for the Week 6 session + authorization toy model."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

import pytest


HERE = os.path.dirname(__file__)
LIVE_QUIZ = os.path.realpath(os.path.join(HERE, ".."))
TEMPLATE = os.path.join(LIVE_QUIZ, "templates", "sim_session_policy.html")
SCRIPT = os.path.join(LIVE_QUIZ, "static", "sim", "session-policy.js")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_template_uses_only_external_script_and_labels_controls():
    src = _read(TEMPLATE)
    assert '<script src="/static/sim/session-policy.js?v={{ asset_v }}"></script>' in src
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>\s*\S", src, re.S)
    assert not re.search(r"\son[a-z]+\s*=", src, re.I)
    assert not re.search(r"\sstyle\s*=", src, re.I)
    for control_id in (
        "rotation-on", "rotation-off", "save-id", "login", "advance-one",
        "advance-four", "use-session", "replay-id", "logout",
        "policy-subject", "policy-action", "policy-object", "policy-rules",
        "policy-identity",
    ):
        assert f'id="{control_id}"' in src


def test_script_has_no_network_storage_or_markup_execution_primitive():
    src = _read(SCRIPT)
    forbidden = (
        "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write",
        "eval(", "Function(", "fetch(", "XMLHttpRequest", "WebSocket",
        "localStorage", "sessionStorage", "document.cookie",
    )
    assert not [term for term in forbidden if term in src]
    assert ".textContent" in src


def _run_node(assertions: str):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is not installed")
    program = (
        "const assert=require('node:assert/strict');"
        f"const api=require({json.dumps(SCRIPT)});"
        + assertions
    )
    subprocess.run([node, "-e", program], check=True, text=True,
                   capture_output=True)


def test_session_rotation_fixation_expiry_and_logout_are_computed():
    _run_node(
        "let m=api.createSessionModel(false);"
        "const pre=m.snapshot().active.id;"
        "m.saveLabel();m.login();m.replaySaved();"
        "assert.equal(m.snapshot().active.id,pre);"
        "assert.equal(m.snapshot().result.tone,'bad');"
        "m=api.createSessionModel(true);m.saveLabel();m.login();"
        "assert.notEqual(m.snapshot().active.id,m.snapshot().savedId);"
        "m.replaySaved();assert.equal(m.snapshot().result.tone,'ok');"
        "m=api.createSessionModel(true);m.login();m.advance(4);"
        "assert.equal(m.snapshot().active,null);"
        "assert.match(m.snapshot().result.detail,/idle timeout/);"
        "m=api.createSessionModel(true);m.login();"
        "m.advance(3);m.touch();m.advance(3);m.touch();"
        "m.advance(3);m.touch();m.advance(1);"
        "assert.equal(m.snapshot().active,null);"
        "assert.match(m.snapshot().result.detail,/absolute lifetime/);"
        "m=api.createSessionModel(true);m.login();m.saveLabel();m.logout();"
        "m.replaySaved();assert.match(m.snapshot().result.detail,/logout/);"
    )


def test_authorization_is_subject_action_object_and_default_deny():
    _run_node(
        "let d=api.evaluateAuthorization('learner-alpha','edit','alpha-note','rules');"
        "assert.equal(d.allowed,true);"
        "d=api.evaluateAuthorization('learner-alpha','edit','beta-note','rules');"
        "assert.equal(d.authenticated,true);assert.equal(d.allowed,false);"
        "assert.match(d.summary,/default deny/);"
        "d=api.evaluateAuthorization('course-admin','view','beta-note','rules');"
        "assert.equal(d.allowed,true);"
        "d=api.evaluateAuthorization('course-admin','edit','beta-note','rules');"
        "assert.equal(d.allowed,false);"
        "d=api.evaluateAuthorization('anonymous','view','public-guide','rules');"
        "assert.equal(d.authenticated,false);assert.equal(d.allowed,true);"
        "d=api.evaluateAuthorization('learner-beta','delete','alpha-note','identity-only');"
        "assert.equal(d.allowed,true);assert.equal(d.flawed,true);"
    )
