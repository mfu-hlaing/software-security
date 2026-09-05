"""Data model for the public, self-paced Weeks 1–6 mastery pathway.

This module does not copy or reinterpret the canonical curriculum files at
runtime. It is a small navigation and practice manifest that points back to the
existing slides, worksheets, simulations, and NoteVault project guide. Nothing
here writes student data. Environment-derived lab URLs are resolved only for a
request and are never stored in the constants below.
"""
from __future__ import annotations

import copy
import os
import re
from collections.abc import Mapping
from urllib.parse import urlsplit


PATHWAY_STAGES = (
    {"id": "learn", "label": "Learn", "verb": "Build the model",
     "description": "Read the core theory and make a prediction in your own words."},
    {"id": "explore", "label": "Explore", "verb": "Watch the mechanism",
     "description": "Manipulate a focused simulation until cause and effect are visible."},
    {"id": "lab", "label": "Lab", "verb": "Collect evidence",
     "description": "Reproduce the weakness only inside the supplied training target."},
    {"id": "defend", "label": "Defend", "verb": "Apply the control",
     "description": "Carry the week's reasoning into a concrete NoteVault improvement."},
    {"id": "check", "label": "Check", "verb": "Retrieve and explain",
     "description": "Use ungraded questions and rationales to expose weak reasoning."},
)


def _resource(label, href, kind):
    return {"label": label, "href": href, "kind": kind}


def _sim(slug, title, prompt):
    return {"slug": slug, "title": title, "href": f"/sim/{slug}", "prompt": prompt}


def _stage(stage_id, title, minutes, summary, completion, *, resources=(),
           simulations=(), launch=None, mission=None):
    label = next(s["label"] for s in PATHWAY_STAGES if s["id"] == stage_id)
    out = {
        "id": stage_id, "label": label, "title": title, "minutes": minutes,
        "summary": summary, "completion": completion,
        "resources": tuple(resources),
    }
    if simulations:
        out["simulations"] = tuple(simulations)
    if launch is not None:
        out["launch"] = launch
    if mission is not None:
        out["mission"] = mission
    return out


def _launch(number, fallback_href, requires_vpn, *, browser_role=None,
            local_required=None):
    return {
        "specific_env": f"MASTERY_WEEK{number:02d}_LAB_URL",
        "base_env": "MASTERY_LAB_BASE_URL",
        "path": f"/week{number:02d}",
        "requires_vpn": requires_vpn,
        "fallback_href": fallback_href,
        "browser_role": browser_role or (
            "The configured URL is an instructor-managed, resettable team "
            "sandbox for bounded browser interaction."
        ),
        "local_required": local_required or (
            "Implement source changes and retain command-line evidence in your "
            "own checkout and submission workflow."
        ),
    }


PROJECT_HREF = "/learn/software-security/doc/project-starter-app"


MASTERY_WEEKS = (
    {
        "id": "week01", "number": 1, "slug": "week01-threat-modeling",
        "title": "Threat Modeling & Security Foundations",
        "strapline": "See the system before chasing bugs",
        "essential_question": "How do we turn a system diagram into a defensible list of security priorities?",
        "minutes": 150,
        "objectives": (
            "Classify security impact using confidentiality, integrity, and availability.",
            "Draw assets, data flows, entry points, and trust boundaries in a useful DFD.",
            "Apply STRIDE and misuse cases, then rank threats by likelihood and impact.",
            "Explain how one reachable input can become an attack path across components.",
        ),
        "terms": ("CIA triad", "asset", "attack surface", "trust boundary", "DFD",
                  "STRIDE", "misuse case", "risk"),
        "owasp": ("A01 Broken Access Control", "A06 Insecure Design"),
        "cwes": ("CWE-22", "CWE-73", "CWE-200"),
        "practice_bank_id": "week01",
        "narrative": "Begin with a model of NoteVault and use it to predict where later attacks will land.",
        "stages": (
            _stage(
                "learn", "Model assets, boundaries, and attacker goals", 30,
                "Start with security objectives and observable data flows. A useful threat model names what matters, where privilege changes, what an attacker controls, and which failure would matter most.",
                "you can explain why a trust boundary is about differing privilege or control—not merely a box or network device.",
                resources=(
                    _resource("Week 1 lecture: Threat Modeling & Security Foundations", "/learn/software-security/week01-threat-modeling/slides", "Slides"),
                    _resource("Week 1 lab overview", "/learn/software-security/week01-threat-modeling/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "Turn the diagram into threats", 35,
                "Move from labels to mechanisms: classify impact, follow attacker-controlled data, name STRIDE threats, use an Elevation of Privilege prompt, and trace a chain across trust boundaries.",
                "you can predict each simulation outcome before running it and explain the result using a component, boundary, and violated security property.",
                simulations=(
                    _sim("cia-triad", "Classify the incident with CIA", "For each incident, name the primary property lost and defend why the other two are secondary."),
                    _sim("path-traversal", "Follow a filename across a boundary", "Predict where an attacker-controlled path resolves before comparing vulnerable and defended handling."),
                    _sim("stride-drill", "Apply STRIDE to one endpoint", "Name the threat from the attacker's capability and affected property—not from a memorized keyword."),
                    _sim("eop-deck", "Prompt a deeper threat conversation", "Connect each card to a real NoteVault element and turn it into a testable misuse case."),
                    _sim("trust-boundary", "Chain threats across the system", "Trace how one weak flow changes privilege and enables the next step in the attack path."),
                ),
            ),
            _stage(
                "lab", "Build and challenge a threat model", 45,
                "Inventory the Week 1 target's reachable inputs and valuable data, draw its DFD, then reason from source and the path simulation or instructor-supplied arbitrary-write demonstration. The worksheet is modeling-first: reproduce the write only when the instructor explicitly authorizes that bounded action in your own disposable sandbox.",
                "your DFD, STRIDE table, and risk ranking refer to the same named flows, and the arbitrary-write threat is supported by a code trace, simulation, or explicitly authorized instructor-demo observation.",
                resources=(
                    _resource("Week 1 threat-modeling worksheet", "/learn/software-security/week01-threat-modeling/worksheet", "Worksheet"),
                    _resource("Threat-model template", "/learn/software-security/week01-threat-modeling/template", "Template"),
                ),
                launch=_launch(1, "/learn/software-security/week01-threat-modeling/worksheet", True),
            ),
            _stage(
                "defend", "Create NoteVault's security map", 25,
                "Use the starter application's registration, login, notes, search, admin, and export flows to establish the map every later defence will reference.",
                "another student can use your diagram and risk register to identify the same top three threats without asking what a component means.",
                mission={
                    "title": "NoteVault release 1: threat model before fixes",
                    "brief": "Draw a DFD with browser, application, database, and external/tooling actors. Mark trust boundaries and attacker-controlled fields. Add at least one STRIDE threat per relevant flow, a misuse case, and a likelihood × impact ranking. Do not fix anything yet—preserve the baseline reasoning.",
                    "repo_path": "project/starter-app (routes, data stores, and Docker boundary)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A versioned DFD, STRIDE table, and top-three risk register with assumptions.",
                },
            ),
            _stage(
                "check", "Retrieve the model without notes", 15,
                "Answer fresh scenarios about boundaries, threat categories, impact, and risk prioritization. Every choice reveals a rationale; the result is private and ungraded.",
                "you can correct a missed answer by pointing to a flow and security property rather than by memorizing the option letter.",
                resources=(_resource("Week 1 ungraded practice", "/learn/software-security/mastery/practice/1", "Practice"),),
            ),
        ),
    },
    {
        "id": "week02", "number": 2, "slug": "week02-sdlc-tooling",
        "title": "Secure SDLC & Security Tooling",
        "strapline": "Turn noisy tools into reliable decisions",
        "essential_question": "Where should each security technique run, and what evidence is strong enough to block a release?",
        "minutes": 140,
        "objectives": (
            "Place threat modeling, review, SAST, SCA, DAST, and fuzzing in a secure delivery lifecycle.",
            "Distinguish a raw finding, a reproducible vulnerability, severity, and business risk.",
            "Triage duplicate and false-positive reports using reachability and evidence.",
            "Design a CI security gate that is strict, explainable, and maintainable.",
        ),
        "terms": ("secure SDLC", "shift left", "SAST", "DAST", "SCA", "fuzzing",
                  "false positive", "triage", "security gate"),
        # These are the planted Week 2 findings. The optional lifecycle gate is
        # mapped separately to A03 in advanced_extension below.
        "owasp": ("A02 Security Misconfiguration", "A04 Cryptographic Failures",
                  "A05 Injection"),
        "cwes": ("CWE-78", "CWE-89", "CWE-327", "CWE-489", "CWE-798"),
        "practice_bank_id": "week02",
        "narrative": "Use the Week 1 risks to choose tools and gates instead of scanning everything without a decision model.",
        "stages": (
            _stage(
                "learn", "Match techniques to lifecycle questions", 30,
                "Threat models guide design; review and SAST inspect code; SCA inspects dependencies; DAST observes a running target; fuzzers search input space. None proves an application is secure by itself.",
                "you can choose a technique from the question it can answer and state what it cannot see.",
                resources=(
                    _resource("Week 2 lecture: Secure SDLC & Tooling", "/learn/software-security/week02-sdlc-tooling/slides", "Slides"),
                    _resource("Week 2 tooling guide", "/learn/software-security/week02-sdlc-tooling/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "Separate crashes and findings from real risk", 25,
                "Inspect live evidence from a fuzz harness and a deliberately noisy finding queue. Reproduce first; group by root cause; then decide severity and release impact.",
                "you can explain why finding count is not vulnerability count and why a crash needs a minimized reproducer.",
                simulations=(
                    _sim("fuzz-verdict", "What actually crashes the harness?", "Predict which bytes reach the dangerous state, then use the computed verdict as evidence."),
                    _sim("triage-drill", "Deduplicate a noisy finding queue", "Group symptom reports by root cause and justify which finding deserves immediate action."),
                ),
            ),
            _stage(
                "lab", "Scan, fuzz, minimize, and triage", 45,
                "Run the supplied scanners as individual direct commands as well as reading the convenience script, whose `|| true` wrappers mask tool exit status. Run the local fuzz harness and preserve versions, commands, raw output, sanitizer trace, and a minimized input. Group duplicate reports without inventing a false positive: dismiss a finding only when contextual evidence actually disproves it.",
                "a classmate can reproduce the confirmed issues, see each individual tool's real exit status, and follow a deduplicated/contextualized disposition that keeps duplicate true findings distinct from genuine false positives.",
                resources=(
                    _resource("Week 2 SDLC/tooling worksheet", "/learn/software-security/week02-sdlc-tooling/worksheet", "Worksheet"),
                    _resource("Week 2 command guide", "/learn/software-security/week02-sdlc-tooling/readme", "Guide"),
                ),
                launch=_launch(
                    2, "/learn/software-security/week02-sdlc-tooling/worksheet", False,
                    browser_role=(
                        "The configured browser URL is an orientation or focused "
                        "interactive landing; it does not run Semgrep, Gitleaks, "
                        "SCA, compilers, sanitizers, or a fuzzer for you."
                    ),
                    local_required=(
                        "Use the checked-out Week 2 lab/toolbox for full scanner "
                        "output, exit status, fuzz corpus, sanitizer trace, and "
                        "minimized-crash evidence."
                    ),
                ),
            ),
            _stage(
                "defend", "Give NoteVault an evidence-based security gate", 25,
                "Convert the Week 1 risks into a lightweight pipeline and triage policy. A useful gate blocks known meaningful failures without training the team to ignore permanent noise.",
                "your gate has a named owner, trigger, severity/reachability rule, evidence artifact, exception expiry, and a test showing one bad change fails.",
                mission={
                    "title": "NoteVault release 2: security checks with a decision policy",
                    "brief": "Run an appropriate SAST or dependency scan against the starter app, deduplicate the output, and write a minimal CI gate. Confirm one issue manually and preserve each tool's status rather than relying on the convenience script's masked exit. Record any genuinely evidenced false positive or accepted risk with an owner and expiry—do not manufacture one—and tie the selected checks back to Week 1 threats.",
                    "repo_path": "project/starter-app (requirements, source, and proposed CI workflow)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A reproducible scan record, triage table, and gate rule demonstrated on one failing case.",
                },
            ),
            _stage(
                "check", "Choose the right evidence and gate", 15,
                "Work through new lifecycle and triage scenarios. Rationales emphasize tool limits, reproducibility, and decisions rather than product names.",
                "you can defend a gate decision with exploitability and evidence, not merely a scanner's color or score.",
                resources=(_resource("Week 2 ungraded practice", "/learn/software-security/mastery/practice/2", "Practice"),),
            ),
        ),
    },
    {
        "id": "week03", "number": 3, "slug": "week03-cryptography",
        "title": "Applied Cryptography for Developers",
        "strapline": "Choose constructions by security goal",
        "essential_question": "What must be secret, unpredictable, unique, or authenticated for cryptography to protect the system?",
        "minutes": 145,
        "objectives": (
            "Distinguish encoding, hashing, password hashing, encryption, and authenticated encryption.",
            "Explain salts, work factors, keys, IVs, and nonces by the property each provides.",
            "Recognize ECB leakage and why confidentiality without integrity is insufficient.",
            "Plan key generation, storage, rotation, and failure handling without inventing cryptography.",
        ),
        "terms": ("hash", "salt", "KDF", "work factor", "AES", "ECB", "CBC",
                  "AEAD", "IV", "nonce", "key management"),
        "owasp": ("A04 Cryptographic Failures",),
        "cwes": ("CWE-327", "CWE-916", "CWE-330", "CWE-798"),
        "practice_bank_id": "week03",
        "narrative": "Protect NoteVault credentials and sensitive notes with standard constructions and an explicit key lifecycle.",
        "stages": (
            _stage(
                "learn", "Map cryptographic tools to properties", 35,
                "Start from the goal: password verification, confidentiality, integrity, authenticity, or transport. Then choose a reviewed construction and satisfy its operational assumptions.",
                "you can state why base64 is not encryption, why a fast digest is poor password storage, and why encryption without authentication permits dangerous modification.",
                resources=(
                    _resource("Week 3 lecture: Applied Cryptography", "/learn/software-security/week03-cryptography/slides", "Slides"),
                    _resource("Week 3 crypto lab guide", "/learn/software-security/week03-cryptography/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "See modes reveal or propagate structure", 20,
                "Compare ECB's independent blocks with chained encryption. Manipulate a block and observe what leaks or changes, then connect the observation to the need for authenticated encryption.",
                "you can predict which repeated plaintext blocks reveal a pattern and explain why a mode's IV or nonce rules matter.",
                simulations=(
                    _sim("aes-modes", "ECB patterns and CBC chaining", "Predict repeated-block output and bit-change propagation before toggling the mode."),
                ),
            ),
            _stage(
                "lab", "Break fragile hashes and unsafe encryption", 45,
                "Crack the supplied weak password hashes and inspect the vulnerable crypto program. Measure rather than assume. Complete password/token fixes locally; for AEAD, add your own decrypt-and-verify path and tamper test—the supplied solution skeleton encrypts but does not provide tag-verifying decryption, and its random fallback key is ephemeral across restarts.",
                "you can show the original failures, explain their property-level causes, and demonstrate that your implemented defended version rejects tampering, prices password guessing appropriately, and uses explicit persistent key configuration when ciphertext must survive restart.",
                resources=(
                    _resource("Week 3 cryptography worksheet", "/learn/software-security/week03-cryptography/worksheet", "Worksheet"),
                    _resource("Week 3 runnable examples", "/learn/software-security/week03-cryptography/readme", "Guide"),
                ),
                launch=_launch(
                    3, "/learn/software-security/week03-cryptography/worksheet", False,
                    browser_role=(
                        "The configured browser URL is an orientation or focused "
                        "mode simulation; it cannot crack the supplied hashes or "
                        "run your password-migration and AEAD code."
                    ),
                    local_required=(
                        "Use the checked-out Week 3 files for hash-tool output, "
                        "ECB block evidence and KDF migration tests; implement "
                        "decrypt/tag verification and explicit persistent key "
                        "configuration yourself before claiming tamper or restart evidence."
                    ),
                ),
            ),
            _stage(
                "defend", "Replace NoteVault's fragile crypto boundary", 30,
                "Treat credential storage, session secrets, and protected note data as separate problems. Use established APIs, migration handling, and environment-backed secrets; do not place a key beside its ciphertext in the repository.",
                "existing users can migrate safely, new password records use a slow salted KDF, tampering fails closed, and the key source and rotation assumption are documented.",
                mission={
                    "title": "NoteVault release 3: passwords and secrets with a lifecycle",
                    "brief": "Identify every digest, token, secret, and encryption operation. Replace fast unsalted password hashing with a supported password-hashing API and design a compatible migration. If note confidentiality is implemented, use AEAD with fresh nonces and external key material. Add tests for wrong passwords, duplicate passwords with distinct salts, and tampered ciphertext.",
                    "repo_path": "project/starter-app (authentication helpers, configuration, and persisted records)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A crypto inventory, migration note, focused patch, and tests demonstrating required failure behavior.",
                },
            ),
            _stage(
                "check", "Reason from properties and assumptions", 15,
                "Use fresh developer scenarios to choose between hashes, KDFs, encryption modes, and AEAD while explaining nonce, salt, and key-management constraints.",
                "you can reject a superficially encrypted design by naming the missing property or broken operational assumption.",
                resources=(_resource("Week 3 ungraded practice", "/learn/software-security/mastery/practice/3", "Practice"),),
            ),
        ),
    },
    {
        "id": "week04", "number": 4, "slug": "week04-injection",
        "title": "Injection: SQL, Commands & Interpreters",
        "strapline": "Keep data out of executable grammar",
        "essential_question": "How does untrusted data change an interpreter's program, and where must structure be fixed?",
        "minutes": 145,
        "objectives": (
            "Trace untrusted input from source to an SQL, shell, or other interpreter sink.",
            "Explain how concatenation changes grammar rather than merely producing a bad string.",
            "Use parameterized SQL and argument-vector APIs, with allowlists where structure must vary.",
            "Assess unrestricted upload as its own file-handling weakness without assuming code execution.",
            "Combine safe construction, least privilege, and regression tests as defence in depth.",
        ),
        "terms": ("source", "sink", "taint flow", "SQL injection", "command injection",
                  "parameterization", "argument vector", "allowlist", "least privilege",
                  "unrestricted upload"),
        "owasp": ("A05 Injection",),
        "cwes": ("CWE-78", "CWE-89", "CWE-434"),
        "practice_bank_id": "week04",
        "narrative": "Close NoteVault's search and export interpreter boundaries without relying on character stripping.",
        "stages": (
            _stage(
                "learn", "Trace data into executable grammar", 30,
                "Injection happens when an interpreter cannot distinguish intended structure from attacker-controlled data. Follow sources to sinks and choose an API that preserves that distinction.",
                "you can explain why escaping and denylisting are context-fragile while parameterized statements fix SQL structure by construction.",
                resources=(
                    _resource("Week 4 lecture: Injection", "/learn/software-security/week04-injection/slides", "Slides"),
                    _resource("Week 4 injection lab guide", "/learn/software-security/week04-injection/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "Watch input alter the SQL parse", 20,
                "Compare a concatenated query with a parameterized one. Focus on the parse tree: the defence works because the database receives code and data through separate channels.",
                "you can predict whether an input becomes a literal value or new syntax before running the simulation.",
                simulations=(
                    _sim("sqli-parse", "How concatenation changes the SQL tree", "Toggle construction methods and explain where attacker text becomes syntax."),
                ),
            ),
            _stage(
                "lab", "Exploit and close two interpreter boundaries", 50,
                "Use the supplied target to reproduce SQL injection and command injection, then compare the supplied parameterized-query and shell-free argument-vector fix. Record two residuals instead of declaring victory: the local container still runs as root, and a leading option-like host (for example `-V`) may still change `ping` behavior unless input/option handling is constrained. Separately show disallowed upload acceptance only; the target neither serves nor executes uploads, so this is not RCE evidence.",
                "the injection cases are re-tested, valid behavior remains, and your report distinguishes what the supplied fix proves from residual root privilege, process-option handling, and upload controls still needed (name, content/type, size, server-owned non-executable storage).",
                resources=(
                    _resource("Week 4 injection worksheet", "/learn/software-security/week04-injection/worksheet", "Worksheet"),
                    _resource("Week 4 local target instructions", "/learn/software-security/week04-injection/readme", "Guide"),
                ),
                launch=_launch(4, "/learn/software-security/week04-injection/worksheet", True),
            ),
            _stage(
                "defend", "Separate NoteVault data from SQL and shell syntax", 30,
                "Review search and export end to end. The fix belongs at the interpreter boundary, with server-side constraints and least privilege—not in a growing list of forbidden characters.",
                "tests contain adversarial quotes, operators, separators, and valid edge cases; every sink uses a structure-preserving API and runs with minimal authority.",
                mission={
                    "title": "NoteVault release 4: safe search and export",
                    "brief": "Trace request values into database and process-execution sinks. Replace SQL string construction with bound parameters. Replace shell command strings with a fixed executable and argument list, validate the small set of allowed export choices, and remove unneeded filesystem/process privilege. NoteVault currently has no upload route: add an explicit architecture test/invariant that no user file enters executable or web-served storage, and apply a full upload policy if your team later adds that feature. Turn the working sandbox inputs into regression tests.",
                    "repo_path": "project/starter-app (search, export, database, and process calls)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A source-to-sink trace, before/after evidence, minimal patch, and injection regression suite.",
                },
            ),
            _stage(
                "check", "Choose controls at the interpreter boundary", 15,
                "Analyze new SQL and command-building snippets. Rationales focus on grammar separation, residual risk, and why superficially sanitized strings still fail.",
                "you can select a fix and identify the independent least-privilege control that limits impact if the fix regresses.",
                resources=(_resource("Week 4 ungraded practice", "/learn/software-security/mastery/practice/4", "Practice"),),
            ),
        ),
    },
    {
        "id": "week05", "number": 5, "slug": "week05-xss-client-side",
        "title": "XSS, Browser Trust & CSRF",
        "strapline": "Defend according to browser context",
        "essential_question": "When the browser mixes data with HTML, JavaScript, URLs, and authenticated requests, which boundary actually prevents execution?",
        "minutes": 145,
        "objectives": (
            "Distinguish reflected, stored, and DOM-based XSS by where unsafe data reaches a sink.",
            "Select output encoding or safe DOM APIs for the exact HTML, attribute, URL, or JavaScript context.",
            "Explain CSP and hardened cookies as defence in depth rather than substitutes for safe rendering.",
            "Prevent CSRF with server-validated tokens, SameSite cookies, and appropriate request design.",
        ),
        "terms": ("same-origin policy", "XSS", "source", "DOM sink", "contextual encoding",
                  "CSP", "HttpOnly", "SameSite", "CSRF token"),
        "owasp": ("A05 Injection", "A01 Broken Access Control"),
        "cwes": ("CWE-79", "CWE-352"),
        "practice_bank_id": "week05",
        "narrative": "Make NoteVault render hostile notes as inert content and reject cross-site state changes.",
        "stages": (
            _stage(
                "learn", "Reason about sources, sinks, and browser contexts", 35,
                "XSS is an execution problem at a rendering sink. The correct defence depends on whether data enters text, an attribute, a URL, script, CSS, or a DOM API. CSRF is different: the browser sends ambient authority on an attacker's request.",
                "you can separate XSS from CSRF and choose a control from the exact browser interpretation context.",
                resources=(
                    _resource("Week 5 lecture: XSS & Client-Side Security", "/learn/software-security/week05-xss-client-side/slides", "Slides"),
                    _resource("Week 5 browser-security guide", "/learn/software-security/week05-xss-client-side/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "Move one value through four browser sinks", 20,
                "Put the same attacker-controlled value into different contexts. Observe that a defence correct for visible HTML text can be wrong inside an attribute, URL, or script context.",
                "you can predict execution from the sink and parser context rather than from whether the value contains a familiar script tag.",
                simulations=(
                    _sim("xss-context", "One value, four sinks", "Predict which parser sees the value and choose a context-matched safe construction."),
                    _sim("csrf-intent", "CSRF is about request intent", "Vary origin/site, ambient session cookies, SameSite, and token validation; distinguish a received unauthenticated POST, a blocked attempt, true CSRF, and an XSS-driven same-origin action."),
                ),
            ),
            _stage(
                "lab", "Prove browser execution, then remove the sink", 45,
                "Exercise the supplied reflected/stored paths and state-changing request. Verify that the defended app makes XSS payloads inert. Its `/comments` POST is unauthenticated, so the still-successful cross-site POST demonstrates missing authentication/request-intent validation—not authenticated ambient-authority CSRF; the fixed cookie's SameSite=Strict setting is not material to acceptance. Use the dedicated browser model or your NoteVault test fixture for true session-bound CSRF reasoning.",
                "the supplied app's XSS payloads render inert, its unauthenticated forged POST is accurately classified as a request-intent/authentication gap, and a separate NoteVault/design test shows an authenticated cross-site state change is rejected without valid server-checked CSRF evidence.",
                resources=(
                    _resource("Week 5 XSS/client-side worksheet", "/learn/software-security/week05-xss-client-side/worksheet", "Worksheet"),
                    _resource("Week 5 local target instructions", "/learn/software-security/week05-xss-client-side/readme", "Guide"),
                ),
                launch=_launch(5, "/learn/software-security/week05-xss-client-side/worksheet", True),
            ),
            _stage(
                "defend", "Make NoteVault hostile-content safe", 30,
                "Trace note, search, and profile values to every template or DOM sink. Prefer automatic escaping and text-safe APIs; add a restrictive CSP, hardened session cookie, and real CSRF validation as independent layers.",
                "tests prove stored and reflected payloads stay inert in their actual contexts and state-changing requests fail when origin/token expectations are absent.",
                mission={
                    "title": "NoteVault release 5: inert notes and intentional requests",
                    "brief": "Inventory server templates and client-side sinks for note titles, bodies, search values, and usernames. Remove unsafe HTML insertion or apply the correct contextual encoder. Add a first-party restrictive CSP without unsafe-inline, set HttpOnly/Secure/SameSite appropriately, and protect every state-changing route with a server-validated CSRF token. Test both attack payloads and normal content.",
                    "repo_path": "project/starter-app (templates, response headers, cookies, and state-changing routes)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A source/sink table, XSS and CSRF regression tests, CSP/cookie evidence, and the focused fix.",
                },
            ),
            _stage(
                "check", "Select the right browser-side boundary", 15,
                "Solve new sink, CSP, cookie, and request-forgery scenarios. Each rationale names the browser behavior that makes the control work or fail.",
                "you can explain the primary control and the defence-in-depth layer without confusing their roles.",
                resources=(_resource("Week 5 ungraded practice", "/learn/software-security/mastery/practice/5", "Practice"),),
            ),
        ),
    },
    {
        "id": "week06", "number": 6, "slug": "week06-authn-authz",
        "title": "Authentication, Sessions & Authorization",
        "strapline": "Verify identity, then enforce every object decision",
        "essential_question": "After a user signs in, what evidence and server-side checks make each sensitive action genuinely authorized?",
        "minutes": 150,
        "objectives": (
            "Separate authentication, session management, and authorization decisions.",
            "Validate JWT signatures and claims under an explicitly allowed algorithm and key.",
            "Recognize IDOR/BOLA and enforce subject–action–object policy on every request.",
            "Design deny-by-default RBAC or attribute/ownership checks and test negative cases.",
        ),
        "terms": ("authentication", "authorization", "session", "JWT", "claim",
                  "signature", "IDOR", "BOLA", "RBAC", "ABAC", "deny by default"),
        "owasp": ("A01 Broken Access Control", "A07 Authentication Failures"),
        "cwes": ("CWE-284", "CWE-639", "CWE-287", "CWE-347", "CWE-321"),
        "practice_bank_id": "week06",
        "narrative": "Finish the six-week arc by making NoteVault verify tokens and enforce ownership/admin policy server-side on every object.",
        "stages": (
            _stage(
                "learn", "Separate identity proof from permission", 35,
                "A valid login or token establishes a subject; it does not authorize every object or action. Sessions and JWTs need integrity, expiry, and lifecycle rules, while each route needs a server-side policy decision.",
                "you can state the subject, action, object, and required policy for a request independently of how the subject authenticated.",
                resources=(
                    _resource("Week 6 lecture: Authentication & Authorization", "/learn/software-security/week06-authn-authz/slides", "Slides"),
                    _resource("Week 6 auth lab guide", "/learn/software-security/week06-authn-authz/readme", "Guide"),
                ),
            ),
            _stage(
                "explore", "Edit a JWT and identify what actually protects it", 20,
                "Decode a token, change its claims, and observe that base64url is only transport encoding. In this vulnerable app, `alg:none` succeeds because code first trusts the unverified header and then explicitly disables signature verification for that branch—not merely because the word `none` appears in a generic algorithm list. A defender pins expected verification behavior before reading attacker-directed policy.",
                "you can distinguish a readable claim from a trusted claim and list the checks needed before it drives access.",
                simulations=(
                    _sim("jwt-forge", "Editing a JWT is not signing it", "Change a role claim, predict the verifier's decision, and name the missing validation when it succeeds."),
                    _sim("session-policy", "Sessions expire; authorization evaluates every action", "Test login rotation, fixation and expiry, then compare identity-only checks with owner/admin/default-deny subject-action-object policy."),
                ),
            ),
            _stage(
                "lab", "Exploit IDOR and weak token verification", 50,
                "Use the supplied JWT-only, read-only target: obtain Alice's valid token, compare her own order with the cross-user IDOR read, then record forged, malformed, and expired-token outcomes against order and admin GET routes. The target has no update/delete actions or server-side session fixture, so do not claim those were tested.",
                "Alice's valid token reads her order, the defended target denies Alice access to Bob's order, forged/malformed/expired tokens fail closed, and an ordinary valid identity cannot reach the admin GET route.",
                resources=(
                    _resource("Week 6 authentication/authorization worksheet", "/learn/software-security/week06-authn-authz/worksheet", "Worksheet"),
                ),
                launch=_launch(6, "/learn/software-security/week06-authn-authz/worksheet", True),
            ),
            _stage(
                "defend", "Enforce NoteVault's subject–action–object policy", 30,
                "Inventory NoteVault's existing create, read, search, export, and admin paths. Resolve the current subject from validated server-side session/identity evidence, load any referenced object, then enforce ownership or role policy before returning data or creating a note. Treat session fixation/rotation and nonexistent update/delete routes as design-only extension work.",
                "a permission matrix maps to centralized checks and negative tests prove an ordinary user cannot read another user's note through the existing API/search/export paths or reach admin behavior, while permitted create/read behavior still works.",
                mission={
                    "title": "NoteVault release 6: verified identity and object-level policy",
                    "brief": "Write a permission matrix for anonymous, user, owner, and admin subjects across NoteVault's actual create, read, search, export, and admin paths. Harden JWT validation, centralize authorization, and apply it to direct and indirect note references. Add two-identity read/role negative tests, expired/tampered token tests, and an audit-safe denial path that does not leak object existence. Document session rotation and hypothetical update/delete policy only as optional design extensions; do not claim runtime evidence for routes the app does not have.",
                    "repo_path": "project/starter-app (login/session code, note routes, admin routes, and tests)",
                    "repo_href": PROJECT_HREF,
                    "deliverable": "A permission matrix, centralized policy patch, and cross-user/token negative-test evidence.",
                },
            ),
            _stage(
                "check", "Make the authorization decision explicit", 15,
                "Work through fresh JWT, ownership, and role-policy scenarios, plus one clearly labeled design-only session-lifecycle extension. Rationales separate identity-evidence validity from the object-level decision that must follow.",
                "you can express each answer as subject + action + object + policy + evidence, including why a valid token alone is insufficient.",
                resources=(_resource("Week 6 ungraded practice", "/learn/software-security/mastery/practice/6", "Practice"),),
            ),
        ),
    },
)


# The canonical slides and worksheets above define what is assessed.  This
# enrichment is deliberately additive: it builds a foundations-to-extension
# learning ladder around those sources without silently turning optional ideas
# into examinable material.  Templates render the structures below directly,
# so the attack/defence models remain ordinary HTML and CSS rather than remote
# diagrams or executable demonstrations.
LAYER_LABELS = ("Foundation", "Core", "Advanced", "Beyond syllabus")


def _layer(label, title, explanation, checkpoint):
    return {
        "id": label.lower().replace(" ", "-").replace("-syllabus", ""),
        "label": label,
        "title": title,
        "explanation": explanation,
        "checkpoint": checkpoint,
        "beyond_syllabus": label == "Beyond syllabus",
    }


def _lane(label, tone, steps, outcome):
    return {
        "label": label,
        "tone": tone,
        "steps": tuple({"label": title, "detail": detail}
                       for title, detail in steps),
        "outcome": outcome,
    }


def _checkpoint(checkpoint_id, title, objective, evidence, xp, hints):
    return {
        "id": checkpoint_id,
        "title": title,
        "objective": objective,
        "evidence": evidence,
        "xp": xp,
        # Hints intentionally point at a reasoning move, never a payload,
        # secret, flag, answer option, or completed patch.
        "hints": tuple(hints),
    }


def _challenge(challenge_id, title, brief, objective, evidence, rank,
               checkpoints):
    checkpoints = tuple(checkpoints)
    return {
        "id": challenge_id,
        "title": title,
        "brief": brief,
        "objective": objective,
        "evidence": tuple(evidence),
        "rank": rank,
        "xp_total": sum(item["xp"] for item in checkpoints),
        "checkpoints": checkpoints,
        "ethics": (
            "Use only the supplied local containers, simulations, your own "
            "NoteVault checkout, or a target explicitly assigned through the "
            "class VPN. Do not test public or third-party systems."
        ),
    }


_ENRICHMENTS = {
    "week01": {
        "topic_coverage": {
            "core": ("CIA and data classification", "assets and attack surface",
                     "use and abuse cases", "DFDs and trust boundaries", "STRIDE",
                     "risk ranking and testable security requirements"),
            "beyond": ("attack trees", "assumption expiry",
                       "continuous threat-model maintenance"),
        },
        "deep_dive": {
            "intro": "Threat modeling is a chain of evidence: protected asset → reachable flow → attacker capability → security impact → testable control. Labels help only when every link names something visible in the system.",
            "layers": (
                _layer("Foundation", "Name value before danger", "Classify NoteVault data by sensitivity and availability need, then state who should be able to read or change it. CIA is an impact vocabulary; it is not a list of attacks.", "Given one incident, name the asset, authorized audience, observed harm, and primary CIA property."),
                _layer("Core", "Draw crossings, not decoration", "A DFD earns its keep when it exposes entry points, processes, stores, identities, and boundaries where trust or privilege changes. Apply STRIDE to a concrete element or flow and write abuse cases from an attacker goal.", "For one browser-to-app flow, identify attacker control, boundary, STRIDE category, and an observable misuse outcome."),
                _layer("Advanced", "Turn threats into decisions", "Attack trees and chained misuse cases show how several modest weaknesses compose. Rank scenarios with explicit likelihood and impact assumptions, then derive a requirement and an abuse-oriented test; a numeric score is not objective truth.", "Explain which assumption would most change the top-three ranking and how the control can be tested."),
                _layer("Beyond syllabus", "Keep the model alive", "Continuous threat modeling reviews architecture diffs, new data classifications, dependency trust, and expired assumptions as the system changes. Mature teams treat the model as versioned engineering evidence, not a one-time diagram.", "Name the code or architecture change that should trigger a model update and the owner who reviews it."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "Continuous threat modeling and attack-tree economics",
            "summary": "Attach model review to design changes and record confidence, uncertainty, control cost, and residual risk. This extends the week's qualitative ranking; it is enrichment, not assumed assessment content.",
            "standards": ("OWASP Top 10:2025 A06 Insecure Design",
                          "ASVS 5.0.0 architecture and threat-modeling controls",
                          "NIST SSDF 1.1 secure design practices"),
        },
        "visual_model": {
            "title": "Filename flow: the same input, two security stories",
            "question": "At which step does attacker-controlled text gain file-system authority?",
            "lanes": (
                _lane("Attack path", "attack", (("Untrusted filename", "A browser chooses a name with path semantics."), ("Naive path construction", "The application joins text without proving containment."), ("Privileged write", "The process creates or overwrites the resolved path with its own file permissions.")), "A low-trust string gains file-write authority outside uploads/, causing integrity or availability impact and possible configuration/code impact where permissions allow."),
                _lane("Defended path", "defense", (("Untrusted filename", "Treat the value as hostile data."), ("Server-owned destination", "Generate a storage name and resolve beneath one allowed root."), ("Containment decision", "Reject anything outside the root before creating the file.")), "The boundary enforces a write-containment invariant that is directly testable with normal and adversarial names."),
            ),
            "caption": "The control belongs at the text-to-path boundary; a firewall or later output encoding cannot restore containment.",
        },
        "challenge": _challenge(
            "w01-map", "Mission 1 · Map before you patch",
            "Create a model that another teammate can use to predict one real sandbox failure and one defensible control.",
            "Connect assets, flows, attacker control, impact, risk, and a testable requirement without editing NoteVault yet.",
            ("Versioned DFD", "ranked misuse case", "prediction versus observed sandbox evidence"),
            "Boundary Scout",
            (
                _checkpoint("model", "Checkpoint 1 · Make trust visible", "Draw the minimum useful DFD and classify important data.", "A diagram with named identities, flows, stores, attacker-controlled fields, and boundaries.", 100, ("Begin with who can send data and who can read it.", "A boundary marks a change in control or privilege, not necessarily a network hop.")),
                _checkpoint("predict", "Checkpoint 2 · Predict a failure", "Write and rank one abuse path before using the lab.", "A misuse case with prerequisites, CIA impact, likelihood/impact assumptions, and expected observation.", 150, ("Follow one input until a more privileged component interprets it.", "If the risk score feels arbitrary, expose the assumption that would move it.")),
                _checkpoint("evidence", "Checkpoint 3 · Test the model", "Compare the arbitrary-write prediction with the first-party path simulation, source trace, or instructor-supplied demonstration; reproduce it only when explicitly authorized in your own disposable sandbox.", "A simulation/demo observation showing create-or-overwrite outside uploads, plus a revised write-containment requirement and negative-test idea.", 250, ("Do not hunt randomly; follow the exact upload-write flow named in the model.", "A strong requirement states an invariant, such as where a newly created file may resolve.")),
            ),
        ),
    },
    "week02": {
        "topic_coverage": {
            "core": ("secure SDLC and shift-left", "SAST, DAST, SCA, IAST and secret scanning",
                     "coverage-guided fuzzing", "sanitizers and crash minimization",
                     "triage, reachability and risk gates"),
            "beyond": ("policy as code", "time-bounded exceptions",
                       "toolchain health and evidence provenance"),
        },
        "deep_dive": {
            "intro": "A security tool answers a bounded question and produces evidence, not truth. The engineering skill is to select the technique, reproduce and deduplicate results, and make an explicit release decision.",
            "layers": (
                _layer("Foundation", "Put feedback where change is cheap", "Threat modeling begins before code; review and SAST inspect implementation; SCA inspects known dependency risk; DAST observes a running surface; IAST combines runtime context with instrumentation. Shift-left means earlier useful feedback, not running every scanner on every keystroke.", "Choose one technique for a design, source, dependency, or runtime question and name its blind spot."),
                _layer("Core", "Triage root causes, not alert counts", "Confirm the code path and configuration, group duplicate symptoms, distinguish false positives from false negatives, and combine technical severity with reachability and business impact. Secret-scanning findings also require revocation, because deleting text does not erase exposure.", "For a scanner alert, record source, sink, reachable path, reproducer, root cause, and disposition."),
                _layer("Advanced", "Make fuzz evidence reproducible", "Coverage guidance rewards inputs that explore new paths; sanitizers expose memory and undefined-behavior faults; minimization removes irrelevant bytes. A crash without the exact build, seed, and smallest reproducer is difficult to debug or regress-test.", "Explain why the minimized input reaches a distinct path and which sanitizer evidence establishes impact."),
                _layer("Beyond syllabus", "Encode release policy", "Policy-as-code can combine severity, exploitability, fix availability, asset criticality, and exception expiry. Gates must distinguish a vulnerable product from a broken scanner and retain versioned evidence so teams do not normalize permanent noise.", "Specify fail-open versus fail-closed behavior for tool outage, plus an owner and expiry for any exception."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "Risk gates as policy, not color thresholds",
            "summary": "Model release decisions with reachability, asset context, confidence, exception ownership, and scanner health. This extends the hands-on SAST/fuzzing work and is clearly optional enrichment.",
            "standards": ("OWASP Top 10:2025 A03 Software Supply Chain Failures",
                          "ASVS 5.0.0 verification and build controls",
                          "NIST SSDF 1.1 implementation and vulnerability-response practices"),
            "browser_labs": (
                _sim("gate-check", "Policy-as-code gate check (from Week 15)",
                     "Optional extension: predict whether each synthetic change passes, then explain the evidence and exception rule. This does not add Week 15 material to the Week 2 assessment."),
            ),
        },
        "visual_model": {
            "title": "Finding pipeline: noise becomes a release decision",
            "question": "Which evidence changes an alert into an actionable, reproducible defect?",
            "lanes": (
                _lane("Uncontrolled queue", "attack", (("Commit", "Code and dependencies change."), ("Raw scanner output", "Overlapping tools emit symptoms and may fail silently."), ("Count-based gate", "A color or alert total decides the build.")), "Duplicates, false confidence, and flaky failures train the team to bypass the gate."),
                _lane("Evidence pipeline", "defense", (("Versioned tools", "Pin rules, dependencies, build flags, and corpus."), ("Triage + reproduce", "Deduplicate by root cause; preserve a minimized proof."), ("Policy decision", "Use reachability, impact, confidence, owner, and expiry.")), "The gate is explainable, regression-testable, and loud when its own evidence source breaks."),
            ),
            "caption": "SAST, DAST, SCA, IAST, fuzzers, and sanitizers observe different slices; their overlap is a feature when triage preserves provenance.",
        },
        "challenge": _challenge(
            "w02-signal", "Mission 2 · Turn signals into a gate",
            "Build a small evidence trail from raw tool output to one defensible NoteVault release decision.",
            "Demonstrate selection, reproduction, deduplication, minimization, and explicit gate behavior.",
            ("versioned commands", "triage table", "minimized reproducer or manual confirmation", "gate decision"),
            "Signal Analyst",
            (
                _checkpoint("observe", "Checkpoint 1 · Preserve raw evidence", "Run only the supplied tools or local harness and capture versioned output.", "Commands, versions, exit status, and unedited finding/crash evidence.", 100, ("Record a tool failure separately from a clean result.", "Different tools may report one root cause from different locations.")),
                _checkpoint("triage", "Checkpoint 2 · Prove and minimize", "Confirm reachability and reduce one result to its essential cause.", "A root-cause grouping and smallest practical reproducer with a disposition for each alert.", 150, ("Ask what observation would falsify the alert.", "For a crash, remove bytes while preserving the same failing path and sanitizer signature.")),
                _checkpoint("gate", "Checkpoint 3 · Encode the decision", "Design a NoteVault gate that fails for the proven issue and handles scanner failure explicitly.", "A policy rule, failing demonstration, owner, evidence artifact, and expiring exception process.", 250, ("A severity label alone cannot establish reachability.", "Test both a vulnerable change and an unavailable/broken tool.")),
            ),
        ),
    },
    "week03": {
        "topic_coverage": {
            "core": ("security goals and primitives", "password KDFs, salt and work factor",
                     "ECB/CBC behavior", "AEAD, nonces and tamper rejection",
                     "CSPRNGs, key lifecycle and TLS", "asymmetric encryption and signatures"),
            "beyond": ("oracle and side-channel thinking", "misuse-resistant APIs",
                       "key/version migration and crypto agility"),
        },
        "deep_dive": {
            "intro": "Cryptography protects a named property only when its construction and operational assumptions hold. Algorithm choice, randomness, key custody, verification order, migration, and error behavior are one system.",
            "layers": (
                _layer("Foundation", "Choose by goal", "Encoding changes representation; hashing fingerprints data; a password KDF deliberately slows guessing; encryption hides data; a MAC or signature authenticates it. Key exchange establishes shared material, while TLS composes several primitives for transport security.", "For a design, state whether it needs confidentiality, integrity, authenticity, password verification, or transport protection before naming an API."),
                _layer("Core", "Satisfy construction rules", "Unique salts prevent shared precomputation but are not secret. Work factors price each guess. AEAD requires a protected key and nonce discipline and must reject an invalid tag before returning plaintext. Tokens require a CSPRNG plus expiry and consumption rules.", "Identify every salt, key, nonce, tag, and random token and state its required property and failure behavior."),
                _layer("Advanced", "Design the lifecycle", "Keys need generation, scoped access, versioning, rotation, recovery, and retirement. Password records need rehash-on-login migration. Signatures bind data to a signer but do not hide it; key exchange needs authenticated identities; TLS validation needs hostname and trust-chain checks.", "Describe how old and new records coexist during rotation without silently decrypting under the wrong key."),
                _layer("Beyond syllabus", "Think like an oracle attacker", "Timing, padding, compression, nonce reuse, and distinguishable error paths can leak information without breaking the primitive's mathematics. Misuse-resistant APIs, uniform failure, and side-channel-aware libraries shrink this attack surface.", "List what an attacker can repeatedly vary and observe, then remove or equalize the sensitive signal."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "Oracle thinking, crypto agility, and migration safety",
            "summary": "Analyze repeated observations, uniform failure behavior, versioned ciphertext, key rotation, and algorithm migration. These ideas deepen the course primitives without becoming hidden quiz scope.",
            "standards": ("OWASP Top 10:2025 A04 Cryptographic Failures",
                          "ASVS 5.0.0 cryptography and data-protection controls",
                          "NIST SSDF 1.1 protected component and configuration practices"),
            "browser_labs": (
                _sim("hash-crack", "Salt and guessing cost (Cryptography Week 2)",
                     "Optional extension: compare identical passwords across stores, measure guesses, and connect the evidence to salts and work factors."),
                _sim("mac-extend", "Length-extension boundary (Cryptography Week 3)",
                     "Optional extension: observe why a raw secret-prefix hash is not a safe MAC and why a reviewed MAC API changes the construction."),
                _sim("cbc-bitflip", "CBC malleability (Cryptography Week 4)",
                     "Optional extension: predict which plaintext region changes when ciphertext is modified, without treating confidentiality as integrity."),
                _sim("dh-mitm", "Authenticated key exchange (Cryptography Week 5)",
                     "Optional extension: separate Diffie–Hellman secrecy from peer authentication by tracing the relay's two independent shared secrets."),
                _sim("padding-oracle", "Uniform failure and AEAD (Cryptography Week 6)",
                     "Optional extension: compare an observable padding decision with tag-first authenticated decryption."),
                _sim("nonce-reuse", "Nonce reuse (Cryptography Week 10)",
                     "Optional extension: manipulate repeated-nonce ciphertexts and state precisely which uniqueness assumption failed."),
                _sim("cert-bypass", "TLS identity validation (Cryptography Week 12)",
                     "Optional extension: decide whether chain, hostname, and trust checks catch an impostor before calling transport secure."),
            ),
        },
        "visual_model": {
            "title": "Protected note: encryption alone versus authenticated encryption",
            "question": "What must the reader verify before releasing any plaintext?",
            "lanes": (
                _lane("Confidentiality only", "attack", (("Plaintext blocks", "Repeated structure enters a deterministic or malleable mode."), ("Ciphertext", "An attacker observes patterns or changes bytes."), ("Decrypt", "The application releases modified or distinguishably failing data.")), "Hiding content does not prove that the ciphertext is fresh, intact, or from an authorized writer."),
                _lane("AEAD boundary", "defense", (("Fresh nonce + context", "Bind record identity/version as associated data."), ("Encrypt + tag", "A reviewed API produces ciphertext and authentication evidence."), ("Verify before release", "Any invalid tag follows one closed failure path.")), "The reader receives plaintext only after integrity and context are established under a protected key."),
            ),
            "caption": "A nonce is not a password and usually need not be secret; its uniqueness rule is construction-specific and must be engineered.",
        },
        "challenge": _challenge(
            "w03-properties", "Mission 3 · Protect properties, not appearances",
            "Audit NoteVault's credentials, tokens, and sensitive data, then prove one safe migration and one closed failure path.",
            "Match each cryptographic use to a goal, satisfy its assumptions, and document its key or record lifecycle.",
            ("crypto inventory", "measured weak baseline", "migration test", "tamper or wrong-secret rejection evidence"),
            "Crypto Custodian",
            (
                _checkpoint("inventory", "Checkpoint 1 · Inventory properties", "Classify every encoding, digest, password record, token, key, and encrypted value.", "A table of goal, primitive/API, secret material, randomness, persistence, and trust boundary.", 100, ("Base64 and JWT segment readability are representation questions, not proof of secrecy.", "Ask what happens if the database leaks separately from application configuration.")),
                _checkpoint("break", "Checkpoint 2 · Demonstrate the missing property", "Use only supplied samples to measure guessing, pattern leakage, or tamper behavior.", "Repeatable local evidence tied to one explicit assumption—not an attack on real credentials or traffic.", 150, ("Compare repeated values or controlled one-bit changes.", "Record what the attacker knows, controls, and observes.")),
                _checkpoint("migrate", "Checkpoint 3 · Migrate and fail closed", "Design a NoteVault patch and regression tests using reviewed APIs.", "Rehash/version migration evidence, separated secret configuration, and wrong-password/tamper negative tests.", 250, ("Migration needs a way to recognize the old record format.", "Never release unauthenticated plaintext before tag verification succeeds.")),
            ),
        ),
    },
    "week04": {
        "topic_coverage": {
            "core": ("taint, source, transformation and sink", "SQL injection",
                     "OS command injection", "parameter binding and argv APIs",
                     "allowlists, least privilege and negative tests",
                     "blind and second-order injection",
                     "unrestricted upload policy and CWE-434"),
            "beyond": ("NoSQL injection", "server-side template injection",
                       "LDAP and expression-language injection"),
        },
        "deep_dive": {
            "intro": "Injection is a parser-boundary failure: attacker-controlled data becomes part of an interpreter's grammar. Trace source to sink, preserve structure as server-owned, and test that hostile data remains data.",
            "layers": (
                _layer("Foundation", "Trace taint to an interpreter", "A source introduces untrusted data, transformations may normalize or store it, and a sink gives it meaning as SQL, shell, HTML, template, or another language. Validation does not change which parser ultimately decides semantics.", "Name source, transformations, sink, interpreter, and authority for one request path."),
                _layer("Core", "Separate data from grammar—and files from execution", "Bind SQL values through prepared statements and launch fixed executables with argument vectors rather than a shell. When identifiers or operations must vary, map an allowlisted public choice to fixed server-owned syntax. Treat unrestricted upload separately: constrain name, content/type, size, storage location, retrieval, and execution permissions. Acceptance alone is CWE-434 risk, not proof of RCE.", "Show the query/argument structure, then state which independent file-upload conditions would have to combine before an accepted file could execute."),
                _layer("Advanced", "Find delayed and quiet execution", "Second-order injection stores apparently harmless input that a later job concatenates; blind injection reveals truth through response differences, timing, or side effects. Least privilege limits blast radius, while negative tests preserve the construction boundary.", "Trace stored data into its later sink and identify the smallest observable signal an attacker could use."),
                _layer("Beyond syllabus", "Generalize beyond SQL and shells", "NoSQL query objects, server-side templates, LDAP filters, and expression languages each have their own grammar and safe construction API. Copying an escaping rule between contexts creates a false sense of separation.", "For a new interpreter, locate its parameterization or structured-builder API and state which fragments remain structural."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "Second-order, NoSQL, template, and LDAP injection",
            "summary": "Apply the same source→transformation→sink model to delayed execution and non-SQL grammars. This is labeled enrichment so students can transfer the mechanism without treating new syntax as assessed recall.",
            "standards": ("OWASP Top 10:2025 A05 Injection",
                          "ASVS 5.0.0 validation, sanitization and encoding controls",
                          "NIST SSDF 1.1 secure implementation and code-review practices"),
        },
        "visual_model": {
            "title": "SQL search: one value, two parse trees",
            "question": "Who owns the query structure when the database parser runs?",
            "lanes": (
                _lane("Concatenated grammar", "attack", (("Request value", "Attacker text enters the search parameter."), ("String assembly", "Code and value become one SQL string."), ("Database parse", "Operators inside the value can alter the program.")), "The application lends database authority to attacker-authored grammar."),
                _lane("Bound value", "defense", (("Request value", "The same hostile bytes remain input data."), ("Fixed statement", "The server defines grammar and a typed placeholder."), ("Bind + execute", "The driver transmits structure and value separately.")), "The parser cannot reinterpret value bytes as a new SQL operator; least privilege limits residual impact."),
            ),
            "caption": "HTML escaping, hidden errors, or a WAF do not create this structural separation at the SQL or shell boundary.",
        },
        "challenge": _challenge(
            "w04-boundary", "Mission 4 · Keep data out of grammar",
            "Trace and prove interpreter-boundary failures in the supplied lab, then construct and negatively test the corresponding NoteVault controls.",
            "Demonstrate structural separation for SQL and process execution, characterize upload acceptance without inventing RCE, and add layered impact reduction.",
            ("source-to-sink trace", "sandbox injection and upload-acceptance observations", "safe construction patch", "negative and authorized-behavior tests"),
            "Interpreter Breaker",
            (
                _checkpoint("trace", "Checkpoint 1 · Draw the parser boundary", "Trace one SQL path and one process path before sending attack input.", "Source, transformations, final sink, interpreter, and executing privilege for both paths.", 100, ("Search for the point where strings become instructions.", "A filter is a transformation; it is not automatically a grammar boundary.")),
                _checkpoint("prove", "Checkpoint 2 · Change meaning safely", "Use only the Week 4 target to show input changes interpreter behavior and that the upload route accepts a disallowed file.", "Exact local request and observable response/side effect plus non-executing upload acceptance/storage evidence, with secrets and flags redacted.", 150, ("Compare a normal request with one that changes the interpreter's parse or chosen operation.", "For upload, stop at accepted/stored evidence: RCE additionally needs a reachable execution handler or executable storage condition that this target lacks.")),
                _checkpoint("separate", "Checkpoint 3 · Prove data stays data", "Patch NoteVault with structured APIs and least privilege, then encode a no-executable-upload invariant or full policy if the feature exists.", "Query/argv construction evidence, hostile-input regressions, one valid-use regression, and a file-handling architecture test.", 250, ("Bind values; map variable identifiers to fixed server-owned fragments.", "For processes, ask whether a shell is needed at all; for files, keep server-generated names and non-executable storage under server policy.")),
            ),
        ),
    },
    "week05": {
        "topic_coverage": {
            "core": ("origin and same-origin policy", "reflected, stored and DOM XSS",
                     "HTML, attribute, URL and JavaScript contexts", "CSP",
                     "CSRF tokens and SameSite", "HttpOnly, Secure and cookie scope"),
            "beyond": ("Trusted Types", "XS-Leaks", "CSP reporting and rollout"),
        },
        "deep_dive": {
            "intro": "The browser runs several parsers under an origin-based authority model. XSS crosses data into executable browser syntax; CSRF causes an authenticated browser to send an unwanted request. They overlap in impact but require different primary controls.",
            "layers": (
                _layer("Foundation", "Reason from origin and parser", "An origin is scheme + host + port. The same-origin policy limits cross-origin reads but does not prevent every cross-origin send. Reflected, stored, and DOM XSS differ in where the unsafe data flow is assembled, not in the victim-side execution authority.", "For a flow, identify the origin, where attacker data is stored/read, the final browser sink, and whether the attacker needs a victim visit."),
                _layer("Core", "Encode for the exact output context", "HTML text, attributes, URLs, CSS, and JavaScript literals have different grammars; one generic escape cannot secure all of them. Prefer safe DOM APIs and framework autoescaping, avoid dangerous sinks, and treat CSP as independent defence in depth.", "Name the final context and the API that keeps the value as text rather than markup or script."),
                _layer("Advanced", "Separate XSS, cookies, and CSRF controls", "HttpOnly limits script reads of a cookie but cannot stop XSS from acting as the user. Secure limits cleartext transport; Domain/Path scope delivery; SameSite reduces cross-site attachment. CSRF tokens bind a state-changing request to the intended site interaction; CSP constrains executable sources.", "For each control, state the specific attacker capability it removes and one capability it leaves."),
                _layer("Beyond syllabus", "Constrain DOM injection and side channels", "Trusted Types can require reviewed producers for high-risk DOM sinks. XS-Leaks infer cross-origin state from timing, navigation, cache, or browser behavior without reading the response. CSP reporting supports staged rollout but reports may contain sensitive URLs.", "Inventory dangerous DOM sinks and observable cross-origin differences before selecting a policy or isolation control."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "Trusted Types, XS-Leaks, and observable browser state",
            "summary": "Explore DOM sink governance and cross-origin side channels after mastering output contexts, CSP, cookies, and CSRF. These topics are optional transfer practice, not hidden Week 5 lab requirements.",
            "standards": ("OWASP Top 10:2025 A05 Injection",
                          "ASVS 5.0.0 browser, cookie and request-integrity controls",
                          "NIST SSDF 1.1 secure implementation and verification practices"),
        },
        "visual_model": {
            "title": "Stored comment: markup authority versus text",
            "question": "Which component finally decides whether a comment is text or executable syntax?",
            "lanes": (
                _lane("Executable sink", "attack", (("Stored comment", "Attacker-controlled bytes persist in the database."), ("Raw template insertion", "The response mixes the value into HTML grammar."), ("Victim browser", "The parser creates executable nodes in NoteVault's origin.")), "The payload acts with the victim page's origin; cookie flags reduce selected consequences but do not remove script authority."),
                _lane("Context-safe render", "defense", (("Stored comment", "The database may still hold hostile text."), ("Text-context encoding", "The renderer emits characters as data for this exact sink."), ("Browser + CSP", "Text remains text; policy independently limits executable sources.")), "Structural output handling stops the injection, while CSP, HttpOnly, SameSite, and CSRF tokens cover distinct residual paths."),
            ),
            "caption": "The database is not where XSS executes. The security boundary is the final value-to-browser-context operation.",
        },
        "challenge": _challenge(
            "w05-origin", "Mission 5 · Defend the browser boundary",
            "Build a context and request-integrity map, observe the supplied XSS and unauthenticated cross-site POST behavior, then use the dedicated model/NoteVault fixture for true authenticated CSRF and layer controls without claiming one header fixes everything.",
            "Distinguish origin, parser context, cookie capability, and forged-request defenses with positive and negative evidence.",
            ("source/sink context matrix", "sandbox browser evidence", "header/cookie inspection", "XSS and CSRF regression cases"),
            "Browser Boundary Defender",
            (
                _checkpoint("contexts", "Checkpoint 1 · Map browser contexts", "Trace reflected, stored, and DOM-style flows to their final sinks.", "A context matrix naming origin, source, storage, sink, parser, and primary encoding/API.", 100, ("The last parser matters more than the first input field.", "A database-stored string can later enter HTML text, an attribute, a URL, or JavaScript—each is different.")),
                _checkpoint("observe", "Checkpoint 2 · Compare attack classes", "In the Week 5 sandbox, contrast an injected-script effect with the unauthenticated `/comments` cross-site POST; then use the dedicated model or NoteVault fixture for session-bound CSRF.", "Bounded observations explaining what the browser sent and parsed, explicitly separating unauthenticated request-intent failure from authenticated ambient-authority CSRF.", 150, ("First ask whether the route requires any identity or authority; `/comments` does not, so cookie attachment cannot explain its acceptance.", "For true CSRF, identify the authenticated state change, ambient credential, cross-site send, and server evidence of user intent; avoid real cookie collection.")),
                _checkpoint("layer", "Checkpoint 3 · Layer and regress", "Harden NoteVault's sinks, content policy, cookies, and state-changing requests.", "Context-specific negative tests plus CSP, cookie, and CSRF evidence with an explicit residual-risk note.", 250, ("Start by removing or structurally neutralizing dangerous sinks.", "Test controls independently: an encoded payload may not exercise CSP, and SameSite is not a server-side CSRF token.")),
            ),
        ),
    },
    "week06": {
        "topic_coverage": {
            "core": ("authentication versus authorization",
                     "JWT algorithm, issuer, audience, expiry and key selection", "IDOR/BOLA",
                     "deny-by-default ownership checks", "RBAC and ABAC",
                     "OAuth 2.0 and OpenID Connect overview"),
            "beyond": ("session lifecycle and fixation (design-only here)",
                       "ReBAC", "passkeys and phishing-resistant MFA",
                       "authorization policy testing at scale"),
        },
        "deep_dive": {
            "intro": "A request crosses two independent gates: establish a subject from trustworthy evidence, then decide whether that subject may perform this action on this object in this context. Either gate can fail while the other appears correct.",
            "layers": (
                _layer("Foundation", "Separate the two gates", "Authentication establishes who is acting; session management carries that fact across requests; authorization evaluates subject, action, object, and context. Changing an object identifier exposes IDOR/BOLA only when the server omits or misapplies the object-level decision.", "For one endpoint, write subject + action + object + policy before considering UI behavior."),
                _layer("Core", "Validate JWTs as identity evidence", "The vulnerable target branches on an attacker-controlled unverified algorithm header and disables signature verification for `none`; that exact branch causes its unsigned-token flaw. The supplied solution pins HS256 and validates audience/expiry. Issuer validation and trusted `kid` selection are advanced enhancements, not claims about the supplied fix. The target supports read authorization evidence only.", "List the supplied algorithm/key/audience/expiry checks, then separately label issuer/key-selection enhancements and the object policy that follows."),
                _layer("Advanced", "Model policy and federation", "Permission matrices expose missing routes and negative cases. RBAC groups permissions by role; ABAC evaluates attributes and context; ownership is a relationship. OAuth delegates API authorization and OpenID Connect adds an identity layer—redirect, state/nonce, PKCE, and token audience still require verification.", "Express an allow rule and at least two deny cases independent of how the user logged in."),
                _layer("Beyond syllabus", "Design session and relationship assurance", "Session fixation/rotation, expiry, revocation, cookie lifecycle, ReBAC, passkeys, and phishing-resistant MFA are design-only extensions here because the supplied JWT target has no server-side session fixture. Stronger identity still does not replace object authorization.", "Sketch a session state transition or relationship rule, label it design-only, and show why a valid high-assurance user can still trigger BOLA."),
            ),
        },
        "advanced_extension": {
            "scope_label": "Beyond Weeks 1–6 syllabus",
            "title": "ReBAC, passkeys, and policy test generation",
            "summary": "Design session rotation/fixation handling, relationship graphs, and stronger authenticators while preserving the rule that every real object action is authorized server-side. These are design-only enrichments beyond the Week 6 runtime target.",
            "standards": ("OWASP Top 10:2025 A01 Broken Access Control and A07 Authentication Failures",
                          "ASVS 5.0.0 authentication, session and access-control controls",
                          "NIST SSDF 1.1 secure design and verification practices"),
        },
        "visual_model": {
            "title": "Private note request: two gates, one decision chain",
            "question": "What does a valid token prove—and what does it leave undecided?",
            "lanes": (
                _lane("Broken chain", "attack", (("Bearer token", "A valid or weakly verified token names Alice."), ("Object lookup", "The route loads note 82 from the URL identifier."), ("Return object", "No owner/action policy runs before serialization.")), "Authentication success is mistaken for universal permission, so Alice can receive Bob's note."),
                _lane("Deny-by-default chain", "defense", (("Verify evidence", "Pin algorithm/key and validate audience/expiry as the supplied fix does; issuer/key selection are advanced hardening."), ("Resolve policy inputs", "Load subject, requested action, object owner/relationships, and context."), ("Authorize then act", "A centralized rule explicitly allows; otherwise return the documented denial.")), "Token integrity and object authorization remain separate gates; uniform non-disclosing denial is an optional enhancement, not behavior claimed for the supplied 403/404 responses."),
            ),
            "caption": "Long random IDs and hidden UI links may slow discovery but are never authorization controls.",
        },
        "challenge": _challenge(
            "w06-policy", "Mission 6 · Prove every permission",
            "Finish NoteVault with strict identity evidence, an explicit permission matrix, centralized enforcement, and two-user negative tests.",
            "Demonstrate JWT validation and read/admin authorization on the supplied target, then enforce NoteVault's actual create, read, search, export, and admin policy paths in your own checkout.",
            ("permission matrix", "JWT validation record", "two-user request matrix", "documented 403/404 behavior plus optional non-disclosing-denial design"),
            "NoteVault Security Engineer",
            (
                _checkpoint("matrix", "Checkpoint 1 · Specify before coding", "Map anonymous, user, owner, and admin subjects to NoteVault's actual note/admin paths.", "An allow/deny matrix for create, read, search, export, and admin; update/delete and session transitions are explicitly marked design-only.", 100, ("Rows can be subjects or roles; columns should be concrete actions on concrete object classes.", "Include negative cases and indirect routes such as search and export, not nonexistent endpoints.")),
                _checkpoint("identity", "Checkpoint 2 · Challenge identity evidence", "Use only the Week 6 target to compare Alice's valid read with forged, malformed, and expired JWT outcomes.", "Redacted request/status evidence for own-order, cross-user order, and admin GETs that identifies which validation or authorization rule decided each.", 150, ("Readable claims are not trusted claims.", "Keep algorithm/key policy and claim semantics separate; this target provides no session-rotation evidence.")),
                _checkpoint("authorize", "Checkpoint 3 · Enforce and cross-test", "Centralize NoteVault policy and test two identities across its existing data disclosures and create path.", "Tests proving an ordinary user cannot read another user's note or reach admin data through API/search/export, while permitted create/read behavior still works.", 250, ("Resolve the target note before deciding ownership, but authorize before returning its fields.", "Use one policy model for direct read, search, export, and admin so a side route cannot drift.")),
            ),
        ),
    },
}


# Copy rather than mutate the literal manifests.  This keeps the source-of-truth
# block readable and gives every caller the same complete public schema.  The
# cumulative value is motivational progress only; no route accepts or grades it.
_BASE_MASTERY_WEEKS = MASTERY_WEEKS
MASTERY_WEEKS = tuple(
    {
        **week,
        **copy.deepcopy(_ENRICHMENTS[week["id"]]),
        "challenge": {
            **copy.deepcopy(_ENRICHMENTS[week["id"]]["challenge"]),
            "cumulative_xp": sum(
                _ENRICHMENTS[item["id"]]["challenge"]["xp_total"]
                for item in _BASE_MASTERY_WEEKS[:index + 1]
            ),
        },
    }
    for index, week in enumerate(_BASE_MASTERY_WEEKS)
)
TOTAL_JOURNEY_XP = sum(week["challenge"]["xp_total"] for week in MASTERY_WEEKS)


def _q(qid, stem, options, correct, rationales, explanation, objective,
       difficulty="Apply"):
    return {
        "id": qid, "stem": stem, "options": tuple(options), "correct": correct,
        "rationales": tuple(rationales), "explanation": explanation,
        "objective": objective, "difficulty": difficulty,
    }


# Original retrieval practice. The canonical graded questions live in
# quizzes/weekly/week01.md … week06.md and are deliberately not imported or
# paraphrased here.
PRACTICE_BANKS = {
    "week01": {
        "id": "week01", "week_id": "week01",
        "title": "Threat-model decisions, not vocabulary",
        "description": "Use a small NoteVault scenario to connect assets, flows, STRIDE, misuse cases, and risk. Select an answer only after you can point to evidence in the system model.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w01-public-export",
                "A NoteVault export endpoint accidentally returns every user's private notes to any signed-in user. Which security objective is the clearest primary impact?",
                ("Confidentiality of note data", "Integrity of the export process", "Availability of the database", "Non-repudiation of the requester"), 0,
                (
                    "Correct: unauthorized readers learn protected note content, so disclosure is the direct harm.",
                    "The response may be produced exactly as coded; no record must be altered for this incident to occur.",
                    "The system remains reachable and serves data, so loss of service is not the primary observation.",
                    "Audit attribution could matter later, but the stated failure is unauthorized disclosure rather than denial of an action.",
                ),
                "CIA labels are useful only when tied to the asset and observed harm. Here the asset is private note content and the direct harm is an unauthorized read.",
                "Classify impact using confidentiality, integrity, and availability.",
                "Understand",
            ),
            _q(
                "w01-flow-threat",
                "A DFD shows Browser → Web App → file storage for an uploaded attachment. The browser controls the filename and the app can create files outside the upload directory. Which threat statement is most actionable?",
                ("Uploads are dangerous", "An attacker may use path segments to make the app create or overwrite a process-writable file outside the attachment directory", "The storage server should use TLS", "The browser is outside the database"), 1,
                (
                    "This names a concern but not a component, attacker action, path, or impact, so it cannot drive a test.",
                    "Correct: it connects attacker control, a boundary-crossing flow, process write privilege, a concrete mechanism, and integrity/availability impact.",
                    "TLS protects a network channel but does not stop the application from resolving an unsafe local path.",
                    "The statement does not describe the relevant upload flow or what an attacker can accomplish.",
                ),
                "A strong threat statement is testable: actor + action + target + precondition + impact. The DFD supplies the exact flow and privilege boundary.",
                "Draw data flows and turn them into testable threats.",
            ),
            _q(
                "w01-risk-order",
                "The team can address only one risk today. Finding A is a styling endpoint crash requiring administrator access; Finding B is an unauthenticated note-download path that works over the Internet. What is the best first decision?",
                ("Fix A because every crash is critical", "Fix B because its exposure, low attack effort, and sensitive-data impact make its current risk higher", "Fix whichever has the larger scanner ID", "Average both findings into one medium risk"), 1,
                (
                    "A crash can matter, but the required administrator access and limited impact must be considered rather than ignored.",
                    "Correct: prioritization combines likelihood/exposure and impact in the actual deployment context.",
                    "Finding identifiers do not measure exploitability or business harm.",
                    "Averaging unrelated risks hides the urgent attack path and produces no defensible work order.",
                ),
                "Severity describes technical harm; risk also includes reachability, prerequisites, assets, and context. Ranking must preserve those assumptions.",
                "Rank threats using likelihood and impact.",
            ),
            _q(
                "w01-misuse",
                "Which scenario is the strongest misuse case for NoteVault's normal “export my notes” use case?",
                ("A user exports their notes as a supported archive", "An attacker changes an export identifier so the service packages another user's notes", "The product owner requests a PDF export option", "A developer renames the export function"), 1,
                (
                    "This is the intended use case and helps define expected behavior, not adversarial abuse.",
                    "Correct: it describes an attacker goal and abuse of the same system interaction, producing a testable authorization requirement.",
                    "This is a feature request, not a hostile goal or security failure.",
                    "An internal refactor does not describe an attacker's action or impact.",
                ),
                "Misuse cases invert a legitimate goal into an adversarial one. Pairing them exposes the security condition the normal story otherwise omits.",
                "Distinguish intended and adversarial system behavior.",
            ),
            _q(
                "w01-chain",
                "A public search parameter reaches an internal worker, and that worker can read the admin database. Why should the DFD show both crossings instead of listing only “search input”?",
                ("More boxes automatically lower risk", "The crossings reveal where control and privilege change, allowing a low-privilege input to be traced into a high-impact attack chain", "STRIDE requires exactly two arrows", "Internal components cannot be threat sources"), 1,
                (
                    "Diagram size does not change security; meaningful flows and boundaries do.",
                    "Correct: threat chaining depends on how attacker influence survives transitions into more privileged components.",
                    "STRIDE provides prompts, not a required number of DFD elements.",
                    "An internal component can carry malicious data, be compromised, or amplify privilege even when it is not the original attacker.",
                ),
                "Trust boundaries make privilege transitions visible. An attack path often matters more than any isolated component finding.",
                "Explain threat chaining across trust boundaries.",
                "Analyze",
            ),
        ),
    },
    "week02": {
        "id": "week02", "week_id": "week02",
        "title": "Tool evidence and release decisions",
        "description": "Triage security signals by what each technique can observe, reproduce the behavior, and turn evidence into a maintainable delivery decision.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w02-unreachable",
                "A static analyzer reports command injection in a debug helper. The helper is excluded from the production image and no build target imports it. What should the reviewer do first?",
                ("Mark it false positive because the scanner is annoying", "Confirm build and reachability evidence, then record it as a real code weakness that is not currently production-exploitable", "Block every release forever", "Run a browser-only DAST scan and ignore the source"), 1,
                (
                    "Tool annoyance is not evidence; the dangerous code may still enter another artifact later.",
                    "Correct: distinguish the weakness from current reachability, preserve evidence, and make an explicit scoped decision.",
                    "A permanent unexplained block creates alert fatigue and does not reflect current deployment context.",
                    "DAST may confirm exposed runtime paths but cannot prove an excluded helper is absent from every build artifact.",
                ),
                "Triage preserves two facts: whether code is weak and whether an attacker can reach it in the reviewed artifact. Those facts drive a time-bounded decision.",
                "Triage findings using reachability and evidence.",
                "Analyze",
            ),
            _q(
                "w02-crash-cluster",
                "A fuzzer saves 400 inputs that all crash at the same stack trace after the same bounds check. Which next step creates the most useful engineering evidence?",
                ("File 400 critical bugs", "Keep the largest input because it contains more bytes", "Deduplicate by root cause and minimize one deterministic reproducer", "Delete the corpus and rerun without instrumentation"), 2,
                (
                    "Crash files are observations; identical root cause should not inflate vulnerability count.",
                    "Large inputs hide the smallest triggering condition and slow diagnosis.",
                    "Correct: a minimized deterministic input plus stack/root cause is reproducible evidence for fixing and regression testing.",
                    "Removing the evidence and instrumentation makes the result harder to reproduce and explain.",
                ),
                "Fuzzing explores input space, but triage turns crashes into engineering work. Deduplication and minimization are part of that conversion.",
                "Deduplicate and minimize fuzzing findings.",
            ),
            _q(
                "w02-runtime-header",
                "The team wants to verify whether the deployed reverse proxy actually omits a required security header. Which technique gives the most direct evidence?",
                ("SAST on a utility module", "SCA on requirements.txt", "DAST or an explicit HTTP check against the running deployment", "Secret scanning of Git history"), 2,
                (
                    "Source analysis may inspect app code but can miss headers added or removed by runtime infrastructure.",
                    "Dependency inventory does not observe the deployed HTTP response.",
                    "Correct: a runtime request sees the combined behavior of application and proxy configuration.",
                    "Secret scanners answer whether credentials are exposed, not which headers a response carries.",
                ),
                "Choose a technique by the system state it observes. Deployment configuration is best checked at the running boundary, while source checks remain complementary.",
                "Place security techniques at the appropriate lifecycle stage.",
            ),
            _q(
                "w02-gate-exception",
                "A critical dependency advisory has no upstream fix, but the vulnerable function is not included in the built artifact. What is the healthiest release-gate response?",
                ("Disable dependency scanning for the repository", "Create a documented, owner-approved, expiring exception tied to artifact/reachability evidence while monitoring for a fix", "Change the advisory severity locally to low", "Copy the vulnerable package into the source tree"), 1,
                (
                    "Disabling the control also hides future reachable vulnerabilities.",
                    "Correct: a narrow, evidence-backed, expiring exception keeps the gate credible without treating context as permanent truth.",
                    "Relabeling upstream severity changes the display, not exploitability, and destroys audit clarity.",
                    "Vendoring does not remove the vulnerable code and can make update tracking worse.",
                ),
                "A gate needs an exception path or teams route around it. Good exceptions are scoped, owned, justified, reviewable, and time-bounded.",
                "Design maintainable CI security gates.",
                "Evaluate",
            ),
            _q(
                "w02-proof",
                "Two scan reports disagree about a possible path traversal. Which artifact best resolves the triage decision?",
                ("The report with the brighter severity color", "A minimal request, exact build/version, observed resolved path, and repeatable response", "The total number of findings in each report", "A screenshot with no command or target version"), 1,
                (
                    "Presentation color is a tool opinion, not proof of runtime behavior.",
                    "Correct: the artifact identifies environment, trigger, mechanism, and observable outcome so another person can reproduce it.",
                    "Finding volume says nothing about this finding's root cause or exploitability.",
                    "A context-free screenshot is difficult to reproduce and may refer to another build.",
                ),
                "Reproducible evidence is the bridge between automated signal and a release decision. Preserve versions and the smallest meaningful trigger.",
                "Distinguish raw findings from confirmed vulnerabilities.",
            ),
        ),
    },
    "week03": {
        "id": "week03", "week_id": "week03",
        "title": "Cryptographic properties under pressure",
        "description": "Choose and operate standard cryptographic constructions by the property the application needs, including their salt, nonce, integrity, and key-lifecycle assumptions.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w03-same-password",
                "During a NoteVault migration, Alice and Bob choose the same password but their new stored password records differ. Under a sound password-hashing design, what is the best explanation?",
                ("One account must have typed the password incorrectly", "Each record uses a fresh random salt while the verifier stores the parameters needed to recompute its slow KDF", "The application encrypted one password with TLS", "The database randomly changes hashes after login"), 1,
                (
                    "Matching passwords need not create matching records; that difference is expected rather than evidence of a typo.",
                    "Correct: unique salts defeat cross-user precomputation and a password-hash record normally carries salt and work parameters.",
                    "TLS protects transport and does not explain different values at rest in the password table.",
                    "Verification records are deterministic for a password, salt, and parameters; uncontrolled random mutation would prevent login.",
                ),
                "A salt is public uniqueness, not a secret key. The slow KDF raises each guess's cost; a distinct salt prevents one precomputed result from covering many users.",
                "Explain salts and password-hashing work factors.",
            ),
            _q(
                "w03-aead-tamper",
                "An application encrypts a note and an attacker flips bytes in the stored ciphertext. Which defended behavior most directly shows authenticated encryption is working?",
                ("The application returns a slightly corrupted plaintext", "The application rejects the record before exposing any unauthenticated plaintext", "The ciphertext becomes shorter", "The encryption key appears in the error log"), 1,
                (
                    "Malleable decryption demonstrates missing integrity; acting on corrupted plaintext can be exploitable.",
                    "Correct: AEAD verifies the tag and fails closed when ciphertext, nonce, or authenticated metadata changes.",
                    "Ciphertext length does not need to change when an attacker flips bytes.",
                    "Logging the key is a severe secret-management failure, not an integrity signal.",
                ),
                "Confidentiality alone does not establish that data is authentic. AEAD binds ciphertext and optional associated data to a verification tag.",
                "Recognize the integrity guarantee of authenticated encryption.",
            ),
            _q(
                "w03-nonce-restart",
                "A service uses AES-GCM with a counter nonce that restarts at zero whenever the container restarts, while retaining the same key. What is the core problem?",
                ("GCM requires the nonce to be secret", "The same key–nonce pair can repeat, violating GCM's uniqueness requirement and endangering confidentiality and integrity", "Counters are always less random than passwords", "Restarting changes the AES algorithm"), 1,
                (
                    "A GCM nonce need not be secret; uniqueness under a key is the critical property.",
                    "Correct: restart-induced reuse breaks a load-bearing operational assumption of the construction.",
                    "Nonce selection is not password selection; predictable counters can be safe if uniqueness is guaranteed.",
                    "The cipher remains AES-GCM; the surrounding nonce lifecycle is what becomes unsafe.",
                ),
                "A secure primitive can fail through state management. Nonce generation must remain unique across restarts, replicas, backups, and key rotation boundaries.",
                "Explain nonce requirements and operational failure modes.",
                "Analyze",
            ),
            _q(
                "w03-key-beside-data",
                "NoteVault commits `APP_KEY` beside its encrypted database so every deployment can decrypt notes. Which change best improves the trust boundary?",
                ("Rename the key file to a hidden filename", "Load key material from a deployment secret mechanism, restrict access, document rotation, and keep ciphertext usable across controlled key versions", "Base64-encode the key before committing it", "Use the same key for password hashing and note encryption"), 1,
                (
                    "Hidden filenames are still copied, readable, and present in repository history.",
                    "Correct: key storage, access, versioning, rotation, and recovery are part of the cryptographic system.",
                    "Encoding changes representation but provides no secrecy.",
                    "Key separation prevents one compromise or misuse from collapsing unrelated security functions; password hashing should not share an encryption key.",
                ),
                "Encryption does not help when the attacker obtains both ciphertext and its key from the same boundary. Key lifecycle is as important as algorithm choice.",
                "Plan secure key generation, storage, and rotation.",
                "Evaluate",
            ),
            _q(
                "w03-ecb-migration",
                "A developer replaces AES-ECB with AES-CBC but does not add authentication. Which review comment is most accurate?",
                ("The change completely solves confidentiality and integrity", "With a fresh unpredictable IV, CBC removes ECB's repeated-block pattern leakage, but unauthenticated ciphertext remains malleable; use a reviewed AEAD construction", "CBC never uses an IV", "ECB is preferable because its output is deterministic"), 1,
                (
                    "CBC addresses one ECB weakness but does not by itself authenticate data.",
                    "Correct: improving pattern hiding is not the same as providing integrity; AEAD supplies both under one reviewed API.",
                    "CBC requires a suitable unpredictable IV; omitting or reusing it creates additional leakage.",
                    "ECB's deterministic block mapping is exactly what reveals repeated structure.",
                ),
                "Evaluate constructions by the whole property set. A migration should also version records and define failure behavior rather than swapping a mode name only.",
                "Recognize ECB leakage and confidentiality-without-integrity risk.",
            ),
        ),
    },
    "week04": {
        "id": "week04", "week_id": "week04",
        "title": "Interpreter boundaries and robust fixes",
        "description": "Trace attacker-controlled data into SQL and process execution, then choose controls that preserve code/data separation and reduce residual impact.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w04-dynamic-sort",
                "A notes endpoint lets a client choose `sort=created_at`. The developer tries to bind the column name as a SQL value parameter, but the database rejects it. What is the safe design?",
                ("Concatenate any client string after removing spaces", "Map a small allowlist of public sort names to fixed SQL identifiers, while binding note values normally", "Disable database errors in production", "HTML-encode the column name"), 1,
                (
                    "Removing spaces does not prevent SQL grammar tokens and leaves structure attacker-controlled.",
                    "Correct: identifiers are SQL structure, so choose them from fixed server-owned fragments; keep data values parameterized.",
                    "Hiding errors may reduce information but does not stop the injected query from executing.",
                    "HTML encoding targets a browser parser, not SQL grammar.",
                ),
                "Placeholders represent data values, not arbitrary grammar. When structure must vary, a strict mapping to fixed server-side choices preserves control of the query.",
                "Use parameterization and allowlists at SQL boundaries.",
                "Analyze",
            ),
            _q(
                "w04-shell-free",
                "The export route must run `/usr/bin/zip` on a server-generated directory and a user-selected archive label. Which invocation has the strongest construction boundary?",
                ("`os.system('/usr/bin/zip ' + label + ' ' + directory)`", "`subprocess.run(['/usr/bin/zip', safe_output_path, directory], shell=False, check=True)` after validating the label and creating the path server-side", "Replace semicolons in the concatenated shell string", "Wrap the whole command in double quotes"), 1,
                (
                    "The shell parses attacker-controlled text as grammar, enabling separators, substitutions, redirections, and option confusion.",
                    "Correct: a fixed executable and argument vector avoid a shell grammar; validation and server-owned paths constrain application semantics too.",
                    "A separator denylist misses many shell features and encoding/normalization variants.",
                    "Shell quoting is context-sensitive and easy to break; it is unnecessary when an argument-vector API fits the task.",
                ),
                "Removing the shell eliminates a parser boundary. Validation still matters for filenames and business rules, and option terminators or server-generated names may be needed.",
                "Use shell-free process APIs and validation.",
            ),
            _q(
                "w04-least-privilege",
                "A parameterized query fix is deployed, but the web application's database account can still drop every table. Why reduce that account's privileges?",
                ("Least privilege replaces the need for parameterized queries", "It limits impact if another query path, dependency, or future regression reaches the database with unintended structure", "Database privileges stop browser XSS", "It makes SQL syntax secret"), 1,
                (
                    "Privilege reduction is defence in depth, not a substitute for safe query construction.",
                    "Correct: independent controls reduce blast radius when a prevention layer fails elsewhere.",
                    "Database grants do not control browser parsing or script execution.",
                    "Security must not depend on hiding SQL syntax, and grants do not hide it.",
                ),
                "A strong fix combines code/data separation with minimal authority and regression tests. Each layer addresses a different failure mode.",
                "Apply least privilege as defence in depth.",
            ),
            _q(
                "w04-second-order",
                "A registration route safely stores a display name using a bound parameter. An admin report later concatenates that stored name into a new query. Can the original name still cause SQL injection?",
                ("No, data that was once parameterized becomes permanently safe", "Yes; stored attacker input becomes dangerous when a later sink reinterprets it as SQL structure", "Only if the name contains HTML", "Only the registration request can be an injection source"), 1,
                (
                    "Parameterization protects one execution boundary; it does not sanitize data for every future context.",
                    "Correct: second-order injection occurs when safely stored hostile data reaches an unsafe later interpreter sink.",
                    "HTML syntax is unrelated to whether the report concatenates SQL grammar.",
                    "Sources include stored or transformed attacker-controlled data, not just the current request object.",
                ),
                "Track trust, not just variables. Untrusted data remains untrusted through storage and needs a safe construction at each interpreter boundary.",
                "Trace tainted data from source to later sinks.",
                "Analyze",
            ),
            _q(
                "w04-filter",
                "A SQL login filter blocks the exact substring `OR` and single quotes. What is the central design flaw?",
                ("The filter is too fast", "It tries to enumerate bad spellings while still letting attacker text share SQL grammar; normalization and alternate syntax can bypass it", "It should block only lowercase input", "It needs a larger database account"), 1,
                (
                    "Performance is not the relevant security property.",
                    "Correct: denylisting payload syntax is brittle because the interpreter still receives mixed code and data.",
                    "Case-specific blocking increases bypasses and still does not establish code/data separation.",
                    "More privilege increases impact and cannot make query construction safe.",
                ),
                "The robust move is structural: keep the query template server-owned and pass user values through the database's binding interface.",
                "Explain why character filters are not a primary injection defence.",
            ),
        ),
    },
    "week05": {
        "id": "week05", "week_id": "week05",
        "title": "Browser contexts and ambient authority",
        "description": "Reason from the browser parser and request model to select safe rendering, CSP, cookie, and anti-CSRF controls without confusing their roles.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w05-dom-render",
                "Client code receives a note title from an API and needs to display it as plain text inside an existing `<h2>`. Which operation best preserves that requirement?",
                ("Assign the title to `innerHTML`", "Set the element's `textContent`", "Pass the title to `eval` before rendering", "Remove only `<script>` substrings and use `innerHTML`"), 1,
                (
                    "`innerHTML` asks the HTML parser to interpret attacker-controlled markup rather than display text.",
                    "Correct: `textContent` creates text, so markup characters remain inert in this sink.",
                    "`eval` creates a JavaScript execution sink and is unrelated to text rendering.",
                    "HTML supports many executable elements, attributes, encodings, and parser tricks beyond one literal tag.",
                ),
                "Prefer APIs whose semantics match the intended output. Plain text should enter a text node, not an HTML parsing boundary.",
                "Select safe DOM APIs for the actual rendering context.",
            ),
            _q(
                "w05-csp-inline",
                "A site safely escapes note text but deploys `script-src 'self' 'unsafe-inline'` so legacy inline handlers keep working. What is the best review conclusion?",
                ("CSP now guarantees XSS is impossible", "Safe rendering remains the primary control, but allowing inline script weakens CSP's independent protection against an injected inline payload", "The policy blocks all first-party scripts", "`unsafe-inline` affects CSS only"), 1,
                (
                    "CSP is defence in depth and this policy deliberately permits a broad class of inline script execution.",
                    "Correct: the escaped sink may be safe, but the policy has less ability to contain another rendering regression.",
                    "`'self'` allows first-party script files; the inline keyword expands execution further.",
                    "The keyword appears in `script-src` and changes script execution, not merely styles.",
                ),
                "CSP should be restrictive and compatible with markup. Moving behavior to first-party script files avoids granting all injected inline code the same privilege.",
                "Explain CSP as an independent defence-in-depth layer.",
                "Analyze",
            ),
            _q(
                "w05-httponly-action",
                "A session cookie is HttpOnly. An XSS payload cannot read the cookie value, but it sends `fetch('/notes/7/delete', {method:'POST'})` from the application's origin. Why can the request still succeed?",
                ("HttpOnly encrypts only half of a cookie", "HttpOnly blocks JavaScript access to the cookie value but the browser can still attach the cookie to same-origin requests", "Fetch never sends cookies", "Deleting a note is not a state change"), 1,
                (
                    "HttpOnly is an access flag, not partial encryption.",
                    "Correct: it limits cookie theft but does not remove the authenticated capabilities available to script already executing in the origin.",
                    "Same-origin fetch uses ambient credentials under the browser's credential rules; the premise observes success.",
                    "Deletion changes server state and needs both authorization and request-forgery protections.",
                ),
                "Cookie hardening limits some consequences; it does not cure XSS. Prevent execution first, then apply authorization and anti-CSRF controls to sensitive actions.",
                "Explain what HttpOnly does and does not prevent.",
                "Analyze",
            ),
            _q(
                "w05-csrf",
                "A profile-update route authenticates with a cookie and accepts a POSTed email address. Which change most directly proves the request was intentionally issued by a page the application rendered?",
                ("Require a server-generated unpredictable CSRF token bound to the user's session and validate it on the POST", "Hide the form's submit button with CSS", "Check that the email contains `@`", "Rename the route to a random-looking word"), 0,
                (
                    "Correct: an attacker site can cause a browser to send cookies but cannot read a session-bound token from the protected origin under the same-origin policy.",
                    "An attacker constructs its own request and is unaffected by the legitimate page's CSS.",
                    "Data validation helps correctness but does not show which origin initiated the authenticated request.",
                    "Endpoints appear in application traffic and code; obscurity is not a request-integrity proof.",
                ),
                "SameSite cookies and origin checks can add layers, but a correctly generated and validated anti-CSRF token is an explicit proof tied to the user's session.",
                "Prevent CSRF with server-validated request tokens.",
            ),
            _q(
                "w05-url-context",
                "A template HTML-escapes a user-controlled profile link before placing it in an anchor's `href`. The value is `javascript:doBadThing()`. What important check is still missing?",
                ("No check; HTML escaping makes every URL safe", "A URL-scheme allowlist or server-generated destination, because HTML encoding does not reject an executable URL scheme", "A database index on the URL", "A slower password KDF"), 1,
                (
                    "HTML encoding protects attribute syntax but does not decide whether the resulting URL scheme is permitted.",
                    "Correct: context safety includes both syntactic encoding and semantic validation of schemes/destinations.",
                    "Database indexing affects lookup performance, not how the browser interprets the link.",
                    "Password storage is unrelated to the URL navigation sink.",
                ),
                "Different parsers can be nested: HTML attribute parsing produces a URL that then has its own semantics. Safe output must account for both layers.",
                "Choose context-aware encoding and URL validation.",
                "Analyze",
            ),
        ),
    },
    "week06": {
        "id": "week06", "week_id": "week06",
        "title": "Identity evidence and object-level policy",
        "description": "Separate token/session validity from the server-side subject–action–object decision required on every sensitive request.",
        "graded": False, "pass_threshold": 0.8,
        "questions": (
            _q(
                "w06-valid-token-object",
                "Alice presents a correctly signed, unexpired JWT and requests `/api/notes/82`, which belongs to Bob. What must the service do after validating the token?",
                ("Return the note because authentication succeeded", "Load or resolve the target and enforce that Alice is its owner or has an explicitly permitted role before returning it", "Trust the note ID because it came from the URL router", "Ask client-side JavaScript to hide Bob's content"), 1,
                (
                    "A valid token establishes Alice's identity; it does not grant permission to every note.",
                    "Correct: authorization evaluates the verified subject, requested action, target object, and policy server-side.",
                    "Routing validates path shape, not ownership or permission.",
                    "The client is attacker-controlled and hiding data after the response has already disclosed it.",
                ),
                "Authentication answers who the subject is. Object-level authorization is a separate decision and must precede the response or state change.",
                "Enforce subject–action–object policy on every request.",
            ),
            _q(
                "w06-token-policy",
                "A JWT verifier confirms a signature but accepts any algorithm named in the token and ignores `exp`, `iss`, and `aud`. Which hardening is strongest?",
                ("Base64-encode the token twice", "Configure an explicit allowed algorithm and verification key, then validate expiration, issuer, audience, and required claims", "Trust tokens with an `admin` field", "Move verification into browser JavaScript"), 1,
                (
                    "Extra encoding provides no authenticity and does not validate claims.",
                    "Correct: the verifier—not attacker-controlled header data—sets trust parameters and checks the claims needed for this service.",
                    "A claim is trusted only after strict cryptographic and semantic validation; its name alone proves nothing.",
                    "Client-side verification can be modified or bypassed and cannot protect the server's resource decision.",
                ),
                "JWT validation has cryptographic and semantic layers. Even a valid token must then feed a separate authorization policy. The supplied Week 6 fix pins HS256 and checks audience/expiry; issuer validation is an advanced enhancement in this scenario.",
                "Extend JWT validation with explicit trust settings beyond the supplied fix.",
                "Advanced",
            ),
            _q(
                "w06-central-check",
                "Five note routes each contain a slightly different ownership `if` statement, and one new export route forgot it. Which design most reduces future authorization drift?",
                ("Add a warning comment to every route", "Centralize a deny-by-default policy helper/decorator that resolves the object and enforces the same action-specific rule, then test every route negatively", "Let the UI omit links users should not click", "Use longer numeric note identifiers"), 1,
                (
                    "Comments do not execute and duplicated policy can still diverge or be omitted.",
                    "Correct: one explicit enforcement path plus route-level negative tests makes missing or inconsistent checks visible.",
                    "Hidden links improve usability but an attacker can still send the HTTP request directly.",
                    "Hard-to-guess identifiers are not authorization and can leak through logs, links, or enumeration.",
                ),
                "Centralization is not sufficient without complete route coverage, but it makes policy reusable, reviewable, and deny-by-default instead of copy-pasted.",
                "Design consistent server-side authorization controls.",
                "Evaluate",
            ),
            _q(
                "w06-session-rotation",
                "A visitor receives an anonymous session ID, signs in, and keeps the exact same session ID afterward. What improvement addresses the resulting session-fixation risk?",
                ("Rotate/regenerate the session identifier when authentication state changes and invalidate the old one", "Display the session ID in the page footer", "Store the ID in a URL parameter", "Make the login button larger"), 0,
                (
                    "Correct: privilege changes should bind to a fresh unpredictable identifier so a value fixed before login cannot ride into the authenticated session.",
                    "Displaying a bearer identifier exposes it to more observers.",
                    "URLs leak through history, logs, analytics, and referrers and worsen session exposure.",
                    "Visual presentation does not change server-side session binding.",
                ),
                "Session security includes issuance, rotation, expiry, revocation, cookie flags, and server-side state—not only password verification. This is design-only extension practice because the supplied Week 6 target is JWT-only.",
                "Design session lifecycle across authentication changes as a beyond-syllabus extension.",
                "Beyond syllabus",
            ),
            _q(
                "w06-denial",
                "For private notes, the team wants to avoid revealing whether another user's note ID exists. Which denial pattern best supports that goal?",
                ("Return the full note with a warning", "Perform the ownership policy before disclosure and return the same not-found response for nonexistent and unauthorized note IDs", "Return 403 with the owner's username", "Let the browser decide after receiving the object"), 1,
                (
                    "The sensitive object has already been disclosed; a warning cannot undo it.",
                    "Correct: uniform denial limits enumeration while the server still records an appropriate internal audit event.",
                    "Naming the owner confirms both existence and identity, increasing information disclosure.",
                    "Authorization must happen before data crosses the server boundary to an attacker-controlled client.",
                ),
                "Status-code choice is context-dependent, but policy must run before response construction and should minimize information leaked to unauthorized subjects. The supplied Week 6 solution distinguishes some 403 and 404 outcomes; uniform denial is an advanced design enhancement, not a claim about that target.",
                "Design an optional non-disclosing denial policy beyond the supplied fix.",
                "Advanced",
            ),
        ),
    },
}


_WEEK_TOKEN = re.compile(r"^(?:week)?0?([1-6])$", re.IGNORECASE)


def _week_number(week):
    if isinstance(week, bool):
        return None
    if isinstance(week, int):
        return week if 1 <= week <= 6 else None
    if isinstance(week, str):
        match = _WEEK_TOKEN.fullmatch(week.strip())
        if match:
            return int(match.group(1))
    return None


def get_week(week: int | str) -> dict | None:
    """Return an isolated copy of one pathway week."""
    number = _week_number(week)
    if number is None:
        return None
    return copy.deepcopy(MASTERY_WEEKS[number - 1])


def get_practice_bank(week: int | str) -> dict | None:
    """Return an isolated copy of one ungraded practice bank."""
    number = _week_number(week)
    if number is None:
        return None
    bank = PRACTICE_BANKS.get(f"week{number:02d}")
    return copy.deepcopy(bank) if bank is not None else None


def _absolute_http_url(value: str, env_name: str) -> str:
    value = value.strip()
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an absolute http(s) URL") from exc
    if (parsed.scheme not in ("http", "https") or not parsed.netloc or
            parsed.username is not None or parsed.password is not None or
            any(ord(ch) < 32 or ch.isspace() for ch in value)):
        raise ValueError(f"{env_name} must be an absolute http(s) URL without credentials")
    if port is not None and not (1 <= port <= 65535):
        raise ValueError(f"{env_name} has an invalid port")
    return value


def lab_url_for(week: int | str,
                environ: Mapping[str, str] | None = None) -> str | None:
    """Resolve a configured local/private lab URL, failing closed on bad input.

    `MASTERY_WEEK01_LAB_URL` … `MASTERY_WEEK06_LAB_URL` take precedence.
    Otherwise `MASTERY_LAB_BASE_URL` is joined to `/week01` … `/week06`.
    Empty values mean "show the checked-in local lab guide".
    """
    number = _week_number(week)
    if number is None:
        return None
    env = os.environ if environ is None else environ
    specific_name = f"MASTERY_WEEK{number:02d}_LAB_URL"
    specific = env.get(specific_name, "")
    if specific and specific.strip():
        return _absolute_http_url(specific, specific_name)
    base_name = "MASTERY_LAB_BASE_URL"
    base = env.get(base_name, "")
    if not base or not base.strip():
        return None
    return _absolute_http_url(base, base_name).rstrip("/") + f"/week{number:02d}"


def resolved_week(week: int | str,
                  environ: Mapping[str, str] | None = None) -> dict | None:
    """Return a week copy with its lab launch URL resolved for this process."""
    result = get_week(week)
    if result is None:
        return None
    for stage in result["stages"]:
        if stage["id"] == "lab":
            stage["launch"]["href"] = lab_url_for(result["number"], environ)
            break
    return result


def validate_data() -> None:
    """Raise ValueError if the static curriculum/practice contract drifts."""
    stage_ids = tuple(s["id"] for s in PATHWAY_STAGES)
    if stage_ids != ("learn", "explore", "lab", "defend", "check"):
        raise ValueError("mastery stage order must be Learn → Explore → Lab → Defend → Check")
    if len(MASTERY_WEEKS) != 6:
        raise ValueError("mastery pathway must contain exactly six weeks")

    seen_sims = set()
    seen_extension_sims = set()
    seen_questions = set()
    seen_checkpoints = set()
    for expected, week in enumerate(MASTERY_WEEKS, 1):
        if week["number"] != expected or week["id"] != f"week{expected:02d}":
            raise ValueError("mastery weeks must be contiguous and correctly identified")
        if tuple(s["id"] for s in week["stages"]) != stage_ids:
            raise ValueError(f"{week['id']} does not contain the exact ordered stage flow")
        defend = week["stages"][3].get("mission")
        if not defend or not defend.get("deliverable") or not defend.get("repo_href"):
            raise ValueError(f"{week['id']} needs a concrete NoteVault defence mission")

        deep_dive = week.get("deep_dive") or {}
        layers = deep_dive.get("layers") or ()
        if tuple(layer.get("label") for layer in layers) != LAYER_LABELS:
            raise ValueError(f"{week['id']} needs all four ordered learning layers")
        if not deep_dive.get("intro") or not all(
                layer.get("explanation") and layer.get("checkpoint")
                for layer in layers):
            raise ValueError(f"{week['id']} has an incomplete deep dive")
        if layers[-1].get("beyond_syllabus") is not True or any(
                layer.get("beyond_syllabus") for layer in layers[:-1]):
            raise ValueError(f"{week['id']} must label only its extension as beyond syllabus")

        extension = week.get("advanced_extension") or {}
        if (extension.get("scope_label") != "Beyond Weeks 1–6 syllabus" or
                not extension.get("summary") or len(extension.get("standards", ())) < 3):
            raise ValueError(f"{week['id']} needs a clearly scoped advanced extension")

        model = week.get("visual_model") or {}
        lanes = model.get("lanes") or ()
        if (len(lanes) != 2 or {lane.get("tone") for lane in lanes} !=
                {"attack", "defense"} or any(len(lane.get("steps", ())) < 3
                                             for lane in lanes)):
            raise ValueError(f"{week['id']} needs a two-lane attack/defence visual model")

        coverage = week.get("topic_coverage") or {}
        if not coverage.get("core") or not coverage.get("beyond"):
            raise ValueError(f"{week['id']} needs explicit core and beyond topic coverage")

        challenge = week.get("challenge") or {}
        checkpoints = challenge.get("checkpoints") or ()
        if (len(checkpoints) != 3 or challenge.get("xp_total") != 500 or
                not challenge.get("brief") or not challenge.get("objective") or
                not challenge.get("evidence") or not challenge.get("rank")):
            raise ValueError(f"{week['id']} needs a complete 500-XP challenge")
        if sum(item.get("xp", 0) for item in checkpoints) != challenge["xp_total"]:
            raise ValueError(f"{week['id']} checkpoint XP does not add up")
        for item in checkpoints:
            token = f"{week['id']}:{item.get('id')}"
            if token in seen_checkpoints:
                raise ValueError(f"duplicate mastery checkpoint {token}")
            seen_checkpoints.add(token)
            if (not item.get("objective") or not item.get("evidence") or
                    len(item.get("hints", ())) < 2):
                raise ValueError(f"{token} needs objective, evidence, and layered hints")
        lab_launch = week["stages"][2].get("launch") or {}
        if not lab_launch.get("browser_role") or not lab_launch.get("local_required"):
            raise ValueError(f"{week['id']} must distinguish browser and local lab work")
        for sim in extension.get("browser_labs", ()):
            if sim["slug"] in seen_extension_sims or sim["slug"] in seen_sims:
                raise ValueError(f"duplicate extension simulation {sim['slug']}")
            if sim.get("href") != f"/sim/{sim['slug']}":
                raise ValueError(f"bad extension simulation link {sim['slug']}")
            seen_extension_sims.add(sim["slug"])
        for stage in week["stages"]:
            for sim in stage.get("simulations", ()):
                if sim["slug"] in seen_sims:
                    raise ValueError(f"duplicate mastery simulation {sim['slug']}")
                seen_sims.add(sim["slug"])

        bank = PRACTICE_BANKS.get(week["practice_bank_id"])
        if not bank or bank.get("graded") is not False:
            raise ValueError(f"{week['id']} needs an explicitly ungraded practice bank")
        if len(bank.get("questions", ())) < 5:
            raise ValueError(f"{week['id']} practice needs at least five questions")
        for question in bank["questions"]:
            if question["id"] in seen_questions:
                raise ValueError(f"duplicate practice question {question['id']}")
            seen_questions.add(question["id"])
            options, rationales = question["options"], question["rationales"]
            if len(options) < 3 or len(options) != len(rationales):
                raise ValueError(f"{question['id']} options and rationales must align")
            if not 0 <= question["correct"] < len(options):
                raise ValueError(f"{question['id']} has an invalid correct option")
            if not all(rationales) or not question.get("explanation"):
                raise ValueError(f"{question['id']} needs complete feedback")

    expected_sims = {
        "cia-triad", "path-traversal", "stride-drill", "eop-deck",
        "trust-boundary", "fuzz-verdict", "triage-drill", "aes-modes",
        "sqli-parse", "xss-context", "csrf-intent", "jwt-forge",
        "session-policy",
    }
    if seen_sims != expected_sims:
        raise ValueError("mastery pathway must contain exactly the 13 Weeks 1–6 simulations")
    expected_extensions = {
        "gate-check", "hash-crack", "mac-extend", "cbc-bitflip", "dh-mitm",
        "padding-oracle", "nonce-reuse", "cert-bypass",
    }
    if seen_extension_sims != expected_extensions:
        raise ValueError("mastery pathway must contain the eight labeled extension simulations")
    if set(PRACTICE_BANKS) != {f"week{n:02d}" for n in range(1, 7)}:
        raise ValueError("practice banks must map one-to-one to Weeks 1–6")
    if TOTAL_JOURNEY_XP != 3000:
        raise ValueError("six mastery challenges must total 3000 local-only XP")


validate_data()
