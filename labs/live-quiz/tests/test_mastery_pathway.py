"""Coverage for the anonymous Weeks 1–6 mastery pathway.

The pathway intentionally sits beside, rather than edits, the canonical slide,
lab, and graded-quiz sources. These tests pin its curriculum mapping, route
security boundaries, configurable lab targets, and stateless practice model.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import mastery_pathway as M
from app import app as flask_app
from routes_content import MASTERY_CSP, PRACTICE_CSP


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


EXPECTED_STAGES = ["Learn", "Explore", "Lab", "Defend", "Check"]
EXPECTED_SIMS = {
    "cia-triad", "path-traversal", "stride-drill", "eop-deck",
    "trust-boundary", "fuzz-verdict", "triage-drill", "aes-modes",
    "sqli-parse", "xss-context", "csrf-intent", "jwt-forge",
    "session-policy",
}


def _all_simulations():
    return [
        sim
        for week in M.MASTERY_WEEKS
        for stage in week["stages"]
        for sim in stage.get("simulations", ())
    ]


def _normalise(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def test_data_validates_and_has_exact_six_week_flow():
    M.validate_data()
    assert [s["label"] for s in M.PATHWAY_STAGES] == EXPECTED_STAGES
    assert [w["number"] for w in M.MASTERY_WEEKS] == list(range(1, 7))
    for week in M.MASTERY_WEEKS:
        assert [s["label"] for s in week["stages"]] == EXPECTED_STAGES
        assert [s["id"] for s in week["stages"]] == [
            "learn", "explore", "lab", "defend", "check"]
        assert week["objectives"]
        assert week["terms"]
        assert week["essential_question"]


def test_every_week_has_layered_depth_visual_transfer_and_challenge():
    ranks = []
    for week in M.MASTERY_WEEKS:
        layers = week["deep_dive"]["layers"]
        assert [layer["label"] for layer in layers] == [
            "Foundation", "Core", "Advanced", "Beyond syllabus"]
        assert all(layer["explanation"] and layer["checkpoint"] for layer in layers)
        assert [layer["beyond_syllabus"] for layer in layers] == [False, False, False, True]

        model = week["visual_model"]
        assert model["title"] and model["question"] and model["caption"]
        assert {lane["tone"] for lane in model["lanes"]} == {"attack", "defense"}
        assert all(len(lane["steps"]) >= 3 and lane["outcome"]
                   for lane in model["lanes"])

        extension = week["advanced_extension"]
        assert extension["scope_label"] == "Beyond Weeks 1–6 syllabus"
        assert len(extension["standards"]) >= 3
        assert week["topic_coverage"]["core"] and week["topic_coverage"]["beyond"]

        challenge = week["challenge"]
        assert challenge["xp_total"] == 500
        assert sum(item["xp"] for item in challenge["checkpoints"]) == 500
        assert len(challenge["checkpoints"]) == 3
        assert all(len(item["hints"]) >= 2 and item["evidence"]
                   for item in challenge["checkpoints"])
        ranks.append(challenge["rank"])
    assert len(set(ranks)) == 6
    assert M.TOTAL_JOURNEY_XP == 3000


def test_current_2025_mappings_and_week5_request_intent_are_truthful():
    assert "A06 Insecure Design" in M.get_week(1)["owasp"]
    assert M.get_week(3)["owasp"] == ("A04 Cryptographic Failures",)
    assert "A01 Broken Access Control" in M.get_week(5)["owasp"]
    lab = next(stage for stage in M.get_week(5)["stages"] if stage["id"] == "lab")
    copy = (lab["summary"] + " " + lab["completion"]).lower()
    assert "unauthenticated" in copy
    assert "not authenticated ambient-authority csrf" in copy
    assert "samesite=strict" in copy


def test_source_specific_limitations_are_not_overclaimed():
    week1_lab = M.get_week(1)["stages"][2]
    assert "modeling-first" in week1_lab["summary"]
    assert "explicitly authorizes" in week1_lab["summary"]
    assert "arbitrary-write" in week1_lab["completion"]

    week2_lab = M.get_week(2)["stages"][2]
    assert "|| true" in week2_lab["summary"]
    assert "without inventing a false positive" in week2_lab["summary"]

    week3_lab = M.get_week(3)["stages"][2]
    assert "your implemented defended version" in week3_lab["completion"]
    assert "does not provide tag-verifying decryption" in week3_lab["summary"]
    assert "ephemeral across restarts" in week3_lab["summary"]

    week4_lab = M.get_week(4)["stages"][2]
    assert "still runs as root" in week4_lab["summary"]
    assert "-V" in week4_lab["summary"]
    assert "not RCE evidence" in week4_lab["summary"]

    week6 = M.get_week(6)
    week6_lab = week6["stages"][2]
    assert "JWT-only, read-only" in week6_lab["summary"]
    assert "no update/delete" in week6_lab["summary"]
    core = week6["deep_dive"]["layers"][1]["explanation"]
    assert "disables signature verification" in core
    assert "Issuer validation" in core


def test_curriculum_cwe_sets_cover_the_actual_planted_flaws():
    assert set(M.get_week(2)["cwes"]) == {
        "CWE-78", "CWE-89", "CWE-327", "CWE-489", "CWE-798"}
    assert set(M.get_week(3)["cwes"]) == {
        "CWE-327", "CWE-916", "CWE-330", "CWE-798"}
    assert "CWE-434" in M.get_week(4)["cwes"]
    assert "CWE-321" in M.get_week(6)["cwes"]


def test_optional_browser_labs_are_explicit_extensions_not_core_simulations():
    expected = {
        "gate-check", "hash-crack", "mac-extend", "cbc-bitflip",
        "dh-mitm", "padding-oracle", "nonce-reuse", "cert-bypass",
    }
    extensions = {
        sim["slug"]
        for week in M.MASTERY_WEEKS
        for sim in week["advanced_extension"].get("browser_labs", ())
    }
    assert extensions == expected
    assert extensions.isdisjoint(EXPECTED_SIMS)


def test_all_thirteen_weeks_one_to_six_simulations_appear_once():
    simulations = _all_simulations()
    assert len(simulations) == 13
    assert {s["slug"] for s in simulations} == EXPECTED_SIMS
    assert len({s["slug"] for s in simulations}) == len(simulations)
    assert all(s["href"] == f"/sim/{s['slug']}" for s in simulations)


def test_each_week_has_a_concrete_notevault_defence_mission():
    deliverables = []
    for week in M.MASTERY_WEEKS:
        defend = next(s for s in week["stages"] if s["id"] == "defend")
        mission = defend["mission"]
        assert "NoteVault" in mission["title"] or "NoteVault" in mission["brief"]
        assert mission["repo_path"].startswith("project/starter-app")
        assert mission["repo_href"]
        assert mission["deliverable"]
        deliverables.append(mission["deliverable"])
    assert len(set(deliverables)) == 6


def test_six_ungraded_practice_banks_have_aligned_rationales():
    assert set(M.PRACTICE_BANKS) == {f"week{n:02d}" for n in range(1, 7)}
    question_ids = set()
    for number in range(1, 7):
        bank = M.get_practice_bank(number)
        assert bank["graded"] is False
        assert len(bank["questions"]) >= 5
        for question in bank["questions"]:
            assert question["id"] not in question_ids
            question_ids.add(question["id"])
            assert len(question["options"]) == len(question["rationales"]) >= 3
            assert 0 <= question["correct"] < len(question["options"])
            assert all(question["rationales"])
            assert question["explanation"]
            assert question["objective"]


def test_practice_stems_do_not_reuse_graded_weekly_questions():
    weekly = Path(__file__).parents[3] / "quizzes" / "weekly"
    graded_stems = set()
    for number in range(1, 7):
        text = (weekly / f"week{number:02d}.md").read_text(encoding="utf-8")
        graded_stems.update(
            _normalise(match.group(1))
            for match in re.finditer(r"^\d+\.\s+(.+)$", text, re.MULTILINE)
        )
    practice_stems = {
        _normalise(q["stem"])
        for bank in M.PRACTICE_BANKS.values()
        for q in bank["questions"]
    }
    assert practice_stems.isdisjoint(graded_stems)


def test_lab_url_precedence_and_resolution(monkeypatch):
    monkeypatch.setenv("MASTERY_LAB_BASE_URL", "https://labs.internal.example/targets")
    assert M.lab_url_for(2) == "https://labs.internal.example/targets/week02"
    monkeypatch.setenv("MASTERY_WEEK02_LAB_URL", "http://10.70.2.25:8080/")
    assert M.lab_url_for(2) == "http://10.70.2.25:8080/"
    resolved = M.resolved_week(2)
    lab = next(s for s in resolved["stages"] if s["id"] == "lab")
    assert lab["launch"]["href"] == "http://10.70.2.25:8080/"


@pytest.mark.parametrize("bad", [
    "javascript:alert(1)", "file:///etc/passwd", "//attacker.example/lab",
    "not a URL",
])
def test_lab_url_rejects_non_http_targets(bad):
    with pytest.raises(ValueError):
        M.lab_url_for(1, {"MASTERY_WEEK01_LAB_URL": bad})


def test_overview_is_prominent_complete_and_tracks_only_local_progress(client):
    response = client.get("/learn/software-security/mastery")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Secure NoteVault across six releases" in body
    assert "13 + 8" in body and "core + optional browser labs" in body
    positions = [body.index(f">{label}<") for label in EXPECTED_STAGES]
    assert positions == sorted(positions)
    for number in range(1, 7):
        assert f'href="/learn/software-security/mastery/week/{number}"' in body
    assert "Six releases. Six defender ranks." in body
    assert "local-only journey XP" in body
    assert '<script src="/static/mastery_journey.js?v=' in body
    assert response.headers["Content-Security-Policy"] == MASTERY_CSP


@pytest.mark.parametrize("number", range(1, 7))
def test_each_week_page_renders_the_full_guided_mission(client, number):
    response = client.get(f"/learn/software-security/mastery/week/{number}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert html.escape(M.get_week(number)["title"]) in body
    assert "NoteVault application mission" in body
    assert "Code-native mechanism map" in body
    assert "Beyond Weeks 1–6 syllabus" in body
    assert "Mission checkpoints" in body
    assert "Mark checkpoint complete" in body
    positions = [body.index(f">{label}<") for label in EXPECTED_STAGES]
    assert positions == sorted(positions)
    assert f'href="/learn/software-security/mastery/practice/{number}"' in body
    assert '<script src="/static/mastery_journey.js?v=' in body
    assert response.headers["Content-Security-Policy"] == MASTERY_CSP


def test_configured_private_lab_link_is_rendered(client, monkeypatch):
    target = "https://week4.vpn.internal.example/lab"
    monkeypatch.setenv("MASTERY_WEEK04_LAB_URL", target)
    response = client.get("/learn/software-security/mastery/week/4")
    assert response.status_code == 200
    assert f'href="{target}"' in response.get_data(as_text=True)


def test_every_internal_curriculum_link_resolves(client):
    links = set()
    for week in M.MASTERY_WEEKS:
        for stage in week["stages"]:
            links.update(r["href"] for r in stage.get("resources", ()))
            links.update(s["href"] for s in stage.get("simulations", ()))
            if stage.get("launch"):
                links.add(stage["launch"]["fallback_href"])
            if stage.get("mission"):
                links.add(stage["mission"]["repo_href"])
        links.update(sim["href"] for sim in
                     week["advanced_extension"].get("browser_labs", ()))
    statuses = {href: client.get(href).status_code for href in sorted(links)}
    broken = {href: status for href, status in statuses.items() if status != 200}
    assert not broken


@pytest.mark.parametrize("number", range(1, 7))
def test_practice_is_anonymous_ungraded_and_first_party_script_only(client, number):
    response = client.get(f"/learn/software-security/mastery/practice/{number}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Ungraded" in body
    assert "nothing is sent to the server" in body
    assert '<script src="/static/mastery_practice.js?v=' in body
    assert "<form" not in body.lower()
    assert "<input" not in body.lower()
    assert "<textarea" not in body.lower()
    assert "<select" not in body.lower()
    assert "student_id" not in body.lower()
    assert "Set-Cookie" not in response.headers
    assert response.headers["Content-Security-Policy"] == PRACTICE_CSP
    assert "script-src 'self'" in PRACTICE_CSP
    assert "form-action 'none'" in PRACTICE_CSP
    assert "'unsafe-inline'" not in PRACTICE_CSP


def test_practice_has_no_write_endpoint(client):
    response = client.post("/learn/software-security/mastery/practice/1", data={"answer": "0"})
    assert response.status_code == 405


def test_practice_javascript_has_no_network_or_identity_api():
    script = (Path(__file__).parents[1] / "static" / "mastery_practice.js").read_text(
        encoding="utf-8")
    assert "localStorage" in script
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "document.cookie",
                      "WebSocket", "EventSource"):
        assert forbidden not in script


def test_practice_saved_state_accepts_only_rendered_questions_and_valid_options():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is not installed")
    script = Path(__file__).parents[1] / "static" / "mastery_practice.js"
    program = f"""
const assert = require('node:assert/strict');
const cleanSaved = require({json.dumps(str(script))}).cleanSaved;
const question = (id, count) => ({{
  dataset: {{questionId: id}},
  querySelectorAll: () => Array.from({{length: count}}, () => ({{}}))
}});
const rendered = [question('q1', 2), question('q2', 3)];
assert.deepEqual(cleanSaved({{q1: 1, q2: 2, stale: 0}}, rendered), {{q1: 1, q2: 2}});
assert.deepEqual(cleanSaved({{q1: -1, q2: 3, stale: 0}}, rendered), {{}});
assert.deepEqual(cleanSaved({{q1: '1', q2: 1.5}}, rendered), {{}});
assert.deepEqual(cleanSaved(null, rendered), {{}});
assert.deepEqual(cleanSaved([], rendered), {{}});
const inherited = Object.create({{q1: 1}});
assert.deepEqual(cleanSaved(inherited, rendered), {{}});
"""
    subprocess.run([node, "-e", program], check=True, capture_output=True,
                   text=True)


def test_journey_javascript_stores_checkpoint_ids_only_and_has_no_network_api():
    script = (Path(__file__).parents[1] / "static" / "mastery_journey.js").read_text(
        encoding="utf-8")
    assert "localStorage" in script
    assert "checkpointId" in script
    for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "document.cookie",
                      "WebSocket", "EventSource", "student_id", "studentId"):
        assert forbidden not in script


def test_path_simulation_models_write_and_real_read_route_status():
    script = (Path(__file__).parents[1] / "static" / "sim" /
              "path-traversal.js").read_text(encoding="utf-8")
    assert "arbitrary-file-write" in script
    assert "CWE-22 / CWE-73" in script
    assert "not served (404)" in script
    assert "blocked (403)" not in script


def test_course_index_and_global_nav_link_to_mastery(client):
    response = client.get("/learn/software-security/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert body.count('href="/learn/software-security/mastery"') >= 2
    assert "Start the mastery path" in body
    assert "Weeks 1–6 mastery" in body


@pytest.mark.parametrize("path", [
    "/learn/no-such-course/mastery",
    "/learn/cryptography/mastery",
    "/learn/software-security/mastery/week/0",
    "/learn/software-security/mastery/week/7",
    "/learn/software-security/mastery/practice/0",
    "/learn/software-security/mastery/practice/7",
])
def test_out_of_scope_mastery_routes_404(client, path):
    assert client.get(path).status_code == 404
