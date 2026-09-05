# Release verification — 2026-09-05

> Historical phase record. The current five-student AWS deployment and later-semester personal targets are documented in [OUTSIDERS-RELEASE.md](OUTSIDERS-RELEASE.md).
## AWS content release — deployment task report

The deployment owner, **Build immersive security labs**, reports that both private team hosts now run integrated commit `8d3e7a9a7e0a637fcdb805f6cce4e4a2b6255e8b`. This was a content-first rollout: only the existing learning service was rebuilt, its data volume was preserved, and pre-cutover backups remain on each host.

- 42 CA-verified HTTPS checks passed across both teams: the mastery page, semester journey and Weeks 1–19. Week 11 workshop content markers also passed.
- Fresh temporary student VPN peers reached their own team and timed out cross-team; the temporary peers were then revoked. Host isolation checks passed.
- Each host reports 13 healthy containers and zero unhealthy containers. Terraform reports no infrastructure changes.
- The temporary rollout VPN container and copied administrator key were removed.

These are the deployment task's reported remote results, separate from the locally executed checks below. They establish the deployed learning content and tested VPN boundaries; they do not establish classroom concurrency capacity or remote operation of the later target pairs.

The six later-semester vulnerable/defended services remain **local only**: zero services from the separate semester stack were launched on AWS. Its 1824 MiB container ceilings plus host overhead do not fit alongside the existing stack on the current 2 GiB team hosts. Dedicated capacity or a reviewed scheduled replacement is still required for these services.

## Application and interface

- Full repository suite: **746 passed, 1 skipped**. The existing skipped test and Eventlet deprecation warning remain; no new runtime migration was attempted.
- All 19 journey pages render, resolve their actual public lecture/worksheet links, reject other course slugs and out-of-range weeks, and keep content escaped.
- Configured target URLs accept only valid absolute HTTPS URLs without embedded credentials. Missing configuration remains explicitly unavailable instead of inventing a target.
- POST does not become a progress or grade submission API. Journey pages set no identity cookie and their CSP blocks network connections from the practice script.
- Real browser checks: Week 10 correct-answer explanation; checkpoint selection; reload preserves the checkpoint and clears in-memory quiz selections; reset clears the test progress; semester map shows all 19 weeks. Visual inspection caught and corrected contrast against the existing dark page background.
- HTTPS browser navigation requires device trust for the private CA. It was not bypassed. UI testing used a separate loopback-only HTTP development preview with a disposable database. The HTTPS checks below used the explicit public CA and normal hostname validation.

## Private runtime

- **15 services** running; **152 HTTPS requests** passed across journey pages, linked materials, simulations and the target pairs.
- API: vulnerable object exposure; defended 401/403/200 ladder; vulnerable privileged-field binding versus defended server-owned fields.
- Chatbot: benign greeting on both services; potentially executable text remains escaped in the guarded HTML output.
- DevSecOps: unauthenticated request succeeds in the deliberately fail-open demo and is denied in the defended one; non-admin denied and seeded admin still allowed.
- All services use non-root UID/GID 10001, read-only roots, dropped capabilities and no-new-privileges. Only the gateway publishes a host port, bound to loopback.
- Each application has a single internal network; the gateway has ingress only; relays have exactly their app network plus ingress. A forged Host request through an app's own relay remains on that app.
- The tested vulnerable API cannot resolve unrelated app/relay names or connect to the Internet or IMDS.
- The runtime smoke checker is checked in at `deploy/semester-labs/smoke.py`; its summary is under `verification/https-smoke-summary.json`.

These checks do not establish remote VPN access, the Linux-host firewall behavior, performance under classroom concurrency, or complete hostile-code containment. Those are explicit gates in the deployment README.

## Week 11 compiler experiment

The existing `softsec-toolbox:latest` image ran with no network, a read-only root and source mount, all capabilities dropped, no-new-privileges, a 384-MiB memory ceiling, one CPU and a 64-PID ceiling. Only disposable `/tmp` was writable/executable so the lab binary could run. No shell-spawning exploit was run.

The shipped harness produced AddressSanitizer's `stack-buffer-overflow` at `fuzz_harness.c:33` inside `strcpy`, reached through the fuzzer entry point at line 51. Exit 1 was the expected detected-crash outcome. Its transcript is `verification/fuzzer-vulnerable.txt`.

A temporary harness copy added a length check before the fixed-size copy. The same bounded fuzz run completed without a sanitizer failure; see `verification/fuzzer-guarded.txt`. This demonstrates the particular boundary check under a short test, not a proof against every possible input. The original lesson source was left intact. The available toolbox did not provide Rust, so the Rust exercise is documented but not claimed as executed here.

## Signing exercise

The verifier's input rejection and exact Cosign identity/issuer arguments passed five tests using a local CLI stub. No registry artifact was signed, no OIDC authentication was performed, and no real signature/provenance verification is claimed. The learner must supply an owned registry artifact and approved signing identity as explained in the supplement.

## Ownership and allocation extension — continuation

The two original native exercises ran using toolbox image `sha256:e0c9c710a8454351bc1d0359bb6a9d7160b08d5d28055519cb03f29ee9af7c64` on Linux ARM64. The non-root, network-free runner checked **15 cases**: expected use-after-free and heap-buffer-overflow reports, defended ordinary/boundary inputs, arithmetic rejection, resource rejection and malformed-input rejection. `verification/memory-workshop.json` records each checked result; `verification/memory-workshop-reports.txt` contains the two actual sanitizer reports. Leak detection is disabled; no exhaustive or concurrency claim is made.

After adding the workshop to the public content registry and Week 11 journey, the relevant content/journey suites passed **154 tests**. The learning image was rebuilt and recreated; the local HTTPS smoke passed **152 requests** including the new workshop, with all 15 services healthy. The earlier full-suite result remains the baseline result; the new continuation used targeted tests and runtime verification.
