# Full-semester learning expansion

## Sources and scope

The canonical local course is the 19-week Software Security sequence at baseline commit `353afa7`. `source-inventory.json` records the available README, worksheet, lecture and lesson-plan sources with hashes and heading inventories across all weeks. `public-crawl.json` records a read-only crawl of 58 public student-document URLs: all returned HTTP 200 on 2026-09-05. The crawl intentionally excludes instructor keys, admin pages and student records. Source availability does not imply every source agrees with every other source.

The new `/learn/software-security/journey` companion preserves the established Weeks 1–6 mastery path and extends the sequence through Week 19. It adds 44 original practice questions, three explanation tiers per week, prerequisite links, code-flow diagrams, concrete source-reading tasks, exercise instructions, evidence requirements and NoteVault transfer tasks. Existing canonical lecture/worksheet pages remain the assessment source. The new material is ungraded preparation.

## What was missing

The first-six-week mastery path already had tiered explanations and good browser simulations. The later materials were navigable documents with less guidance for moving from a concept into source, an observed behavior and a verified defence. Beginning learners need a small conceptual model before command execution; advanced learners need explicit assumptions and ways to test whether a control generalizes.

Each week now follows: explain → trace → predict → experiment → defend → retrieve. The interface offers 15-minute and 45-minute study paths alongside a deeper worksheet session. Advanced sections disclose more detail on demand. Progress tracks three self-checks per week, not reading time or competitive speed; it remains browser-local and has no connection to a grade. Hints guide investigation; original questions give explanations after an attempt. Revision weeks add error categorization and reattempts.

## Source conflicts and limitations surfaced

| Topic | Evidence from detailed material | How the journey handles it |
|---|---|---|
| Week 7 mock | Six challenges; omits the ECB oracle present in Week 9 | Explicitly distinguishes practice from assessed coverage |
| Week 10 API | Vulnerable orders route performs no auth check; defended code trusts a toy client identity header | Teaches authorization while explicitly requiring verified identity for production |
| Week 11 memory | Shipped routines demonstrate stack overflow and format string flaws | Adds a separate optional ownership/allocation workshop with two native bugs, defended counterparts and 15 bounded checks |
| Week 12 resolver | Simulation, not a deployed malicious registry | Teaches its stated resolver assumptions and real-tool limits |
| Week 12 signing | Legacy script uses wildcard signer filters and local image examples | Adds strict, digest-bound verification guide and executable verifier |
| Week 14 AI | Deterministic mock, not a model service or MCP server | Separates observed mock results from real-agent security claims |
| Week 17 mock | Eight challenges versus twelve in Week 19; no direct DevSecOps/project challenge | Adds separate written-design/project revision instead of claiming identical final coverage |
| Week 18 scope | Detailed lecture emphasizes Weeks 10–15; Week 16 is studio | Uses the detailed blueprint and original preparation exercises |
| Week 19 delivery | Recording before session plus three-minute Q&A | Distinguishes the final delivery from Week 16’s live rehearsal |

## Practice delivery matrix

| Weeks | Browser pathway | Executable practice |
|---|---|---|
| 1–6 | Existing mastery + expanded semester explanations and retrieval | Existing team targets, first-party simulations, local scanner/KDF/code workflow |
| 7–9 | Review and assessment preparation with published briefs | Reuse first-half mock/assigned targets; no new graded service or exam answers |
| 10 | API theory, mass-assignment model, practice | Isolated vulnerable/defended API pair; 401/403/200 and field-binding tests |
| 11 | Stack model, code tracing, boundary questions | Toolbox/VM compiler and fuzzer; intentionally no shared remote shell |
| 12 | Resolver model, inventory/signing reasoning | Local scanner/SBOM plus identity-scoped registry verification; OIDC requires the learner’s setup |
| 13 | IAM and infrastructure reasoning | Local configuration review/scanning and private-infra access checks |
| 14 | Layered prompt model and tool-policy design | Isolated vulnerable/guarded deterministic chatbot pair |
| 15 | Gate model, release and logging reasoning | Isolated fail-open/fail-closed service pair plus learner-owned CI workflow |
| 16–19 | Studio, review, preparation and handover | Project evidence and instructor-run assessments; practice progress never becomes a grade |

## Infrastructure and release boundaries

`deploy/semester-labs` is a separate Compose project with one loopback HTTPS listener on 9443, its own database and CA volumes, seven isolated application networks and fixed-upstream relays. It can be tested without restarting the other task’s 8443 stack. Its total container memory ceilings are 1824 MiB before host overhead; this is not a concurrency/load guarantee.

The existing AWS pilot uses one VPN edge and dedicated team hosts. This work does not apply a second Terraform stack or modify the other task’s live deployment. Remote rollout requires the deployment owner to integrate the tested content commit and choose a capacity-reviewed lab stack. Running both complete stacks on a 2-GiB host is not supported. The release runbook records concrete integration, rollback and VPN/TLS checks.

## Primary technical references checked

- [OWASP API Security project](https://owasp.org/www-project-api-security/) — course API taxonomy.
- [OWASP LLM01 prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — direct/indirect injection and application control boundaries; course labels remain the 2025 taxonomy.
- [SLSA 1.2 specification](https://slsa.dev/spec/v1.2/) — distinguish signed artifacts from evidenced build requirements.
- [Sigstore verification](https://docs.sigstore.dev/cosign/verifying/verify/) — exact signer and issuer constraints.
- [LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html) — harness-driven fuzzing and bounded local execution.
- [Docker bridge networking](https://docs.docker.com/engine/network/drivers/bridge/) — user-defined bridges and published-port reachability.

## Remaining deeper expansions

The 19-week journey is a guided companion, not a claim that every advanced topic now has a full production-grade environment. Future bounded additions should include a verified-identity API exercise, distributed rate-limit behavior, an actual private package registry, native FFI and asynchronous-ownership exercises, real-model prompt-injection evaluation, and isolated CI runners. Each needs its own threat model, cost/capacity decision and positive/negative test evidence. The current release labels these limits rather than simulating a successful experiment.
