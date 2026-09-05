# Outsiders live demo upgrade - 5 September 2026

The private AWS NoteVault target now has a responsive Outsiders notes workspace with real note cards, JSON links, search results, an accessible composer, sign-in/error pages and a practice loop. It uses local CSS with no external UI asset dependency. The deliberate project exercise behavior remains intact. The academy still serves all 19 weeks, and its expiry wording now correctly measures 60 minutes from launch.

Deployed application checkout: `dc18b82`. NoteVault candidate image built from `941aa8d`. The public [machine-readable verification](verification/outsiders-ui-demo.json) contains sanitized current evidence. The [full baseline release](OUTSIDERS-RELEASE.md) and [VPN handover](ACCESS-AND-DEMO.md) remain applicable.

## Changes and verification

- Eight meaningful NoteVault request-flow checks passed locally and on both AWS candidate images: normal/failed login, create/search/JSON, logout, registration and preservation of the intended exercise behaviors. Existing pinned-library deprecation warnings remain.
- Actual browser use over the student's private WireGuard peer created a note, searched for a unique word and returned that note. The narrow 304-pixel content pane had matching client/scroll widths; the notebook no longer overflows the page.
- A real DeepSeek response explained the forgeable teaching identity and linked the selected Week 10 source. Browser models remain labeled as explanations, not target execution.
- The current student audit rechecked all 19 rooms and 88 linked resources, normal CA/hostname verification, owner access, other-slot denial with forged forwarding headers and cross-team TCP denial.
- The active target retained non-root/read-only/capability, memory, CPU, PID and fixed-network controls. Target-origin connections to the Internet, external DNS, metadata, broker, host SSH and another slot were denied.
- Both brokers were active and all current service containers were running without OOM flags. The JSON records memory and service snapshots.
- Terraform validate reported zero errors/warnings. An authenticated plan proposed no changes (exit 0). Refresh observed the designed post-bootstrap IMDS shutdown, ignored by the existing metadata lifecycle rule, plus empty-tag normalization. No apply or fresh-infrastructure recreation was performed.
- The installer now rebuilds NoteVault from the reviewed application release; a bootstrap pinned to an older commit no longer leaves the old project UI image in a newly installed personal runtime.

## Redirect regression

The legacy Flask target returned an absolute redirect to its internal fixed relay origin after login. Caddy now rewrites only that slot's fixed `http(s)://pN-app:5000/` response Location into a relative path. Normal upstream identity and fixed-relay isolation remain intact. Both generated gateways validated; the actual student login now returns `302 Location: /`. The gateway change passed 34 targeted campus checks earlier in this demo session.

## Demo state and capture method

The first attempted target backup failed before a reset, so the note captured in the screenshot was recreated. Additional uncaptured edits from that first target cannot be claimed as preserved. Later refreshes used a verified SQLite backup/restore and retained four total seeded/demo notes. Future updates must stop if backup verification fails. Academy accounts, coursework and progress use separate persistent storage.

macOS system-wide VPN activation required administrator input. Instead, an isolated local Docker WireGuard client used the student's existing profile. A loopback-only viewing bridge fetched the real AWS HTTPS services with the supplied CA and exact hostname verification; no browser certificate warning was bypassed. Its local ports are not shareable student URLs. Regular access uses each student's own WireGuard profile, team CA and private HTTPS hostname.

The 798-test full release, eleven target choices on both hosts and five-client isolation/concurrency checks are earlier baseline evidence. This visual upgrade reran the affected request flows and live boundaries, not a new full-semester load test. There is no cold-provisioning or feature-parity claim with commercial training platforms.
