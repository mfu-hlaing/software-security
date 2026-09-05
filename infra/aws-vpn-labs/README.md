# AWS private lab pilot

This module creates a deliberately small, single-AZ pilot: one public
WireGuard/NAT edge and one private EC2 lab host per team. It is infrastructure
for authorized coursework, not an Internet-facing vulnerable-app platform.

```text
Internet
   | UDP 51820 only
   v
WireGuard edge (public subnet, source/dest check disabled)
   | 10.66.0.x identity preserved; nftables allowlist
   +----------------------+----------------------+
   v                                             v
team1 private subnet                          team2 private subnet
10.60.10.10:8443                             10.60.20.10:8443
team1 /32s + instructor only                 team2 /32s + instructor only
```

**Current application runtime:** after Terraform bootstrap, follow the [personal academy installer](../../deploy/personal-labs/README.md) to deploy the 19-week academy and five individual practice slots. Terraform remains pinned to the reviewed bootstrap commit; the separately reviewed application release is checked out and installed in place. Do not change the bootstrap ref just to upgrade the UI, because that can replace team instances.

The original bootstrap creates a learning app and Week 1/4/5/6 targets. Weeks 2
and 3 use first-party interactive browser labs plus local-checkout tool work,
not shared shells.
Only the matching NoteVault team profile starts on each host. Private DNS uses
the reserved `labs.test` suffix.

## Security invariants

- The edge is the only instance with a public IPv4 address. Its public security
  group has only the configured WireGuard UDP rule—no HTTP and no SSH.
- WireGuard `AllowedIPs`, edge nftables, team security groups, and dedicated
  subnets all enforce the fixed peer-/32-to-team mapping. Instructor `/32` is
  the sole identity allowed to private SSH and both teams.
- VPN-to-VPC packets are not masqueraded. Explicit team-subnet return routes
  preserve the `/32` identity security groups inspect.
- Lab EC2 instances have encrypted EBS, no public addresses, and IMDSv2 with
  hop-limit 1 only during cloud-init. A one-action role disables IMDS before
  Docker starts; bootstrap fails closed if that cannot be confirmed.
- The repository URL is restricted to public GitHub HTTPS and the ref must be a
  full commit SHA. The private nodes retry until edge NAT is ready, verify the
  fetched SHA, and build only the clean `repo/` checkout.
- Application containers have distinct internal Docker bridges and no host
  ports. Each bridge has one hardened fixed-upstream relay; shared Caddy joins
  only a separate ingress bridge and is the only stack process published on
  `0.0.0.0:8443`. The relay cannot choose an upstream from Host/SNI/request
  data, closing the application-layer pivot from the command-injection lab.
  Explicit host firewall rules deny off-subnet traffic from every Docker subnet.

Read [RUNBOOK.md](RUNBOOK.md) before applying and [THREAT-MODEL.md](THREAT-MODEL.md)
before admitting students.

## Contents

- `network.tf`, `compute.tf`: VPC, routing, security groups, edge, two lab hosts
- `cloud-init/`: fail-closed WireGuard and immutable pinned-repo bootstrap
- `scripts/create-peer-config.sh`: student-device key/config generation
- `scripts/onboard-peer.sh`, `scripts/revoke-peer.sh`: public-key lifecycle
- `scripts/reset-team-target.sh`: instructor-only disposable target reset
- `scripts/smoke-peer-isolation.sh`: positive own-team and negative cross-team test
- `scripts/smoke-host-isolation.sh`: container, Caddy-pivot, ping, and mastery-link tests
- `terraform.tfvars.example`: public/non-secret input shape only
- `backend.tf.example`: remote encrypted state pattern

Scripts are intentionally runnable as `bash scripts/<name>.sh`; they need not
be executable in a source archive.
