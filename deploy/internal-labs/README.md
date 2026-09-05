# Private small-cohort lab stack

This is a deployment wrapper for the existing Week 1, 4, 5, and 6 targets,
NoteVault, and the learning platform. It does not make intentionally vulnerable
code safe for the public Internet. Its security boundary is the VPN plus a
dedicated, disposable lab host.

Weeks 2 and 3 use manipulable first-party browser labs plus the worksheets and
practice already served under `/learn`. Their full scanner/fuzzer and crypto
toolchains run from each student's local checkout; the shared host does **not**
expose a shell or Docker daemon. This avoids turning Docker access into root
access on a multi-user host.

## Local configuration check

1. Copy `.env.example` to `.env` and replace every secret placeholder.
2. Add the example `labs.test` hostnames to the local hosts file, pointing to
   `127.0.0.1`. `.test` is reserved for testing and cannot collide with a public
   DNS name.
3. Run `docker compose --env-file .env -f compose.yml --profile all-teams up --build`.
4. Browse to `https://learn.pilot.labs.test:8443`. Caddy uses an internal
   CA; install `caddy_data`'s root certificate only on managed lab devices.

The default bind address is loopback. The AWS bootstrap sets `0.0.0.0` on a
private EC2 interface whose security group accepts HTTPS only from the assigned
WireGuard peer addresses.

## Isolation properties

- Vulnerable application ports are not host-published at all. Caddy's 8443 is
  the sole host-published application socket (loopback locally; all interfaces
  only on the VPN-protected AWS host).
- Every target has a distinct hostname and a distinct `internal: true` Docker
  network containing only that target and one fixed-purpose relay. Caddy joins
  a separate ingress network and never a target network. A Week 4 command
  injection can reach its own relay, but the relay's upstream is an
  operator-owned environment value fixed to Week 4—not Host, SNI, or a request
  URL—so every request loops back to Week 4.
- Current Docker does not activate published ports on `internal` bridges. The
  trusted Caddy/relay ingress bridge is therefore non-internal. No vulnerable
  app joins it, and the AWS host's `LAB-CONTAINER-GUARD` blocks off-host traffic
  from its explicit subnet.
- Application roots are read-only. Required state is tmpfs, except the learning
  platform's named data volume and Caddy's internal CA.
- Containers run as UID 10001, drop all capabilities, set no-new-privileges,
  and have CPU, memory, and PID ceilings.
- The active single-team profile's aggregate container memory ceilings stay
  below 2 GiB; AWS also serializes image builds to avoid a t3.small bootstrap
  OOM. This is a small-cohort capacity target, not a load-test guarantee.
- Remote image commands call Flask with `debug=False`; lesson source files are
  unchanged.
- The two NoteVault services are profile-gated and network-isolated. On AWS,
  each team host starts only its matching profile.
- Vulnerable-target state and Week 4/6 flags are shared by members of the same
  team. They are team challenges, not identity-bound individual scoring. An
  instructor can force-recreate an allowlisted target with the AWS runbook's
  reset helper; mastery XP remains private browser-local self-tracking.

## Important limitations

- Docker containers are not a complete hostile-code boundary. The AWS design
  therefore gives each team a separate disposable EC2 host and a dedicated
  subnet/security group.
- Caddy's private CA must be trusted on client devices. Each host currently has
  its own CA; a centrally managed private PKI is a future improvement.
- Caddy and the relays are trusted infrastructure. A proxy vulnerability could
  cross targets on the same team's host. Their Dockerfiles build the reviewed
  Caddy 2.11.4 source commit with exact patched Go modules and Go 1.26.6, then
  copy it into an upgraded digest-pinned Alpine runtime. Rebuild and rescan
  these images whenever the Go, Alpine, or Caddy advisories change.
- Upstream advisory GHSA-6365-7ppr-5r92 affects configurations that combine
  `forward_auth` and `reverse_proxy` before Caddy 2.11.5. These Caddyfiles do not
  use `forward_auth`, so the affected handler combination is unreachable here;
  move to the first reviewed 2.11.5+ release when it is available.
- Compose environment values are visible to host administrators through Docker
  inspection. They must be lab-only secrets, never AWS or institutional keys.
- SQLite, uploads, and in-memory Socket.IO games keep the learning service
  single-replica. Back up the whole encrypted host volume and restore-test it;
  do not add replicas without moving state to shared purpose-built services.
- Base images are digest-pinned, but Python transitive dependencies are not yet
  hash-locked. CI should generate and verify lockfiles before a wider rollout.

Before a cloud rollout, scan the trusted control-plane images with a current
vulnerability database. Fixed HIGH or CRITICAL findings are a deployment
blocker; findings in intentionally vulnerable lesson images require separate,
documented reachability/teaching-purpose review:

```sh
trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --exit-code 1 software-security-internal-labs-caddy:latest
trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --exit-code 1 software-security-internal-labs-learning-relay:latest
```

The narrowly scoped NoteVault exception and its required controls are recorded
in [`VULNERABILITY-EXCEPTIONS.md`](VULNERABILITY-EXCEPTIONS.md).
