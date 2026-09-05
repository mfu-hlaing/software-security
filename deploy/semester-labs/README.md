# Private semester lab release

The `/learn/software-security/journey` route covers all 19 weeks. This separate stack hosts the learning app plus paired Week 10 API, Week 14 deterministic chatbot and Week 15 DevSecOps targets. It preserves the existing fixed-upstream relay isolation design and does not start a shared shell or attach a Docker socket to student-facing services.

## Local deployment

From the repository root:

```bash
python3 deploy/semester-labs/setup.py
docker compose --env-file deploy/semester-labs/.env -f deploy/semester-labs/compose.json build
docker compose --env-file deploy/semester-labs/.env -f deploy/semester-labs/compose.json up -d --wait
```

Open `https://learn.semester.localhost:9443/learn/software-security/journey`. Browsers normally resolve `.localhost` to loopback; if your resolver does not, add the hostnames listed in `compose.json` to your local hosts configuration. All seven HTTPS hostnames need the same private CA trusted on the managed learner device. Export its **public root certificate**, never the CA key:

```bash
docker compose --env-file deploy/semester-labs/.env -f deploy/semester-labs/compose.json \
  cp gateway:/data/caddy/pki/authorities/local/root.crt deploy/semester-labs/root.crt
openssl x509 -in deploy/semester-labs/root.crt -noout -fingerprint -sha256
```

Verify the fingerprint through the instructor before importing that certificate into the appropriate device/browser trust store. The repo never changes your global certificate trust. The smoke check uses this CA explicitly and does not disable certificate validation.

```bash
python3 deploy/semester-labs/smoke.py
```

The default binds only `127.0.0.1:9443`. This is private to the development computer, **not yet a remotely reachable class deployment**. It uses separate images, networks and data volumes from the Weeks 1–6 stack on 8443. To pause it without deleting data:

```bash
docker compose --env-file deploy/semester-labs/.env -f deploy/semester-labs/compose.json stop
```

## What the browser labs demonstrate

- API: BOLA, field binding and bounded rate limiting. The defended service's `X-User-Id` remains a toy identity; the relay causes its per-IP counter to be team-shared.
- AI: deterministic prompt-handling and escaping layers, not an actual LLM or MCP server.
- DevSecOps: fail-open versus fail-closed authorization and structured logs. Real CI runs in each learner's own repository.
- Week 11 binaries, Week 12 signing, Week 13 scanner work: the journey supplies explanations and local-tool exercises. No terminal-in-browser or fabricated command output.
- Practice flags and mutable target state are team-shared, not graded per-student captures. The journey never claims local self-checks prove assessed work.

## Integrate with the existing private AWS pilot

The task deploying Weeks 1–6 owns the initial AWS rollout. Do not run a second Terraform apply or replace its active host while that deployment is in progress. There are two concrete release options:

1. **Content first:** integrate this branch, rebuild only the existing `learning` service, retain its data volume and existing lab URLs. All 19 journey pages and simulations become available immediately at the existing VPN HTTPS origin. Later target-pair links remain explicitly unconfigured until the target services exist.
2. **Modern-stack lab phase:** run this semester stack on a dedicated capacity-reviewed team host or replace the first-half stack during a scheduled maintenance window. Save the old image IDs, Compose environment, database/uploads backup and CA volumes first. Never use `down -v` as an upgrade/reset step. This stack's fresh learning database is separate by default; preserve the old service or explicitly configure its data-volume migration after a backup/restore check.

For the second option on an already protected AWS team host:

- Use the same reviewed repository commit on each team host. Build serially (`COMPOSE_PARALLEL_LIMIT=1`) on small hosts, or build images outside them and deploy reviewed digests.
- Set `SEMESTER_BIND_ADDRESS` to that host's private IP and `SEMESTER_HTTPS_PORT=8443`, since the existing VPN/firewall rules permit that port. Only one gateway can occupy it.
- Set `SEMESTER_LEARN_HOST=learn.team1.labs.test` (or team2) and the six `SEMESTER_{API,AI,OPS}_{VULNERABLE,DEFENDED}_HOST` values to names under the same team's DNS zone. The existing VPN DNS uses per-team wildcard zones.
- Install the reviewed `install-egress-guard.sh` and `semester-egress-guard.service` at the shown `/opt/software-security` path, `chmod 0750` the script, then enable the service before starting containers. It covers this stack's explicit `172.29.0.0/24` through `172.29.7.0/24` networks. Revalidate after a Docker restart. Check for route/subnet conflicts first.
- Preserve the existing edge WireGuard peer-/32 rules, team security group, no-public-IP property and disabled IMDS. Never open HTTP/HTTPS to the public Internet as a shortcut.
- The combined container ceilings here are 1824 MiB, excluding the OS and build processes. This is only a small-cohort pilot. Both complete stacks together exceed a 2-GiB team's budget; do not co-locate them without a reviewed capacity change. Actual simultaneous-user load and larger cohorts are not validated by smoke tests.
- Test from an actual student peer: own team succeeds, other team fails, disconnection removes access. Confirm unauthorized public access fails; inspect security-group rules as well as network observations.
- Test from every target: other app/relay DNS names fail; external IPs, metadata and host gateway sockets are unreachable; a forged Host to its own fixed relay still returns that same target.
- Test from the gateway and a relay that Internet and IMDS egress are blocked by the Linux firewall guard. Local Docker Desktop testing alone cannot prove the AWS firewall behavior.
- Distribute only the public CA certificate via the existing instructor onboarding flow. Confirm trusted hostname verification from learner devices. Preserve CA keys only in the protected host volume/backups.

The remote release is usable only after both positive access and negative isolation checks pass. A successful Terraform plan or local HTTPS request is not proof of remote student access.

## Reset, backup and rollback

Reset only one disposable target with `docker compose ... up -d --force-recreate api-vulnerable` (or the exact AI/ops service). In-memory user mutations and demo rate counters reset; the learning volume is unaffected. Do not reset during another learner's active exercise.

Back up SQLite consistently, plus the upload directory and protected CA volume, using the existing instructor runbook. Verify a restore before any migration. For rollback, stop the semester gateway, restore the prior environment/image configuration and start the previous stack. Retain all data volumes; verify the old learning app and VPN isolation before announcing recovery.
