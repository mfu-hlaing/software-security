# Threat model: private intentionally vulnerable labs

## Scope and assumptions

The pilot assumes students are authorized but untrusted occupants of their own
team environment. They may exploit every documented weakness—including Week
4 command execution—and may accidentally run destructive payloads. The public
Internet is hostile. The instructor workstation and AWS administrator account
are trusted, patched, and protected with MFA.

The objective is to protect AWS credentials, the EC2 host, the other team,
course records, and the public Internet while preserving the intended lab
behavior. Preventing a team from damaging its own disposable lab is not a goal.

## Assets and trust boundaries

| Asset / boundary | Main risk | Controls in this pilot |
|---|---|---|
| Public edge | Scanning or direct access to vulnerable HTTP/SSH | Only UDP 51820 in the edge security group; WireGuard authenticates before any private service is reachable; nftables input defaults to drop. |
| Peer identity | One team impersonates another | One key and fixed `/32` per device; WireGuard cryptographically binds source addresses; disjoint slot checks; immediate server-side revocation. |
| Team boundary | Team 1 reaches Team 2 | Separate subnets and security groups plus nftables `/32` rules; no VPN masquerade; negative peer smoke test. |
| Host boundary | Command injection reaches host, proxy, metadata, or Internet | Internal Docker bridge per target; read-only/non-root/cap-drop/no-new-privileges; bridge-to-host and Docker egress guards; IMDS disabled before containers start. |
| Lab boundary | One vulnerable target pivots through a shared proxy | Targets have no host ports. Each internal app bridge has one hardened relay with an operator-fixed upstream back to that same app; shared Caddy joins only the separate ingress bridge. |
| Browser boundary | Lab XSS steals real sessions or sends data outside VPN | Distinct hostnames reduce origin sharing. Students must use a dedicated browser profile with no real accounts/data. Browser Internet egress is not controlled by this stack. |
| Supply chain | Moving ref or contaminated build context ships secrets/code | Full commit SHA; public HTTPS URL validation; SHA verification; root `.dockerignore` starts deny-all; Docker build context is the checked-out `repo/`, never the parent workspace. |
| State/data | Keys, roster, grades, or uploads leak | Terraform takes public keys and opaque IDs only; client private keys stay on clients; EBS encryption; `.gitignore` excludes state, peer configs, `.env`, and uploads. |

## Abuse cases and expected result

1. An unauthenticated Internet client probes the EIP: it sees only a silent or
   authenticated WireGuard UDP endpoint; there is no public TCP listener.
2. A team-one peer connects directly to team two by IP or DNS: edge nftables
   drops it and the team-two security group independently lacks that `/32`.
3. Week 4 executes a reverse shell or scans RFC1918/metadata: its internal
   Docker network has no external route; defense-in-depth rules reject VPC and
   metadata destinations if that network is accidentally changed.
4. Week 4 sends its relay another lab's Host/SNI: the relay ignores it for
   routing and connects only to `week04:5000`. Week 4 shares no network with
   ingress peers, and host firewall rules reject cross-subnet/off-host traffic.
5. A peer config is copied: revoke its opaque name immediately; do not reuse
   the `/32` until `wg-peer-admin list` and an isolation test confirm removal.
6. An SSRF targets IMDS: the endpoint is disabled before containers start and
   Docker cannot route to metadata. The attached role has no data permissions.

## Residual risks and limits

- Containers share one kernel per team. A kernel/container-runtime escape can
  own that team's host. Separate EC2 hosts limit but do not eliminate impact.
- Caddy and the relays are trusted infrastructure. A proxy compromise could
  reach every relay on that same team host. The trusted binary is built from an
  exact reviewed Caddy source commit with fixed-version Go security updates and
  digest-pinned builder/runtime bases; scan the result before each rollout.
  The relay design prevents request-controlled routing, not a proxy-runtime
  exploit.
- Caddy advisory GHSA-6365-7ppr-5r92 is not reachable because neither the
  ingress nor relay Caddyfile uses `forward_auth`; both use fixed
  `reverse_proxy` routes only. Upgrade from 2.11.4 to the first reviewed 2.11.5+
  release rather than adding the affected handler combination.
- The edge is a single point of failure and a small NAT instance, not an HA or
  high-throughput design. nftables/dnsmasq state is on its root volume.
- The private hosts need outbound HTTP/HTTPS during bootstrap. Containers are
  blocked, but a host compromise can use that host egress.
- Internal Caddy CAs are host-local. Installing a CA root expands trust on that
  browser/device; use managed course profiles and remove roots after the term.
- Browser-side exfiltration is outside container controls. Week 5 must use fake
  data and a dedicated browser profile with no institutional sessions.
- Exercise state and generated Week 4/6 flags are shared within a team host,
  not identity-bound per student. Treat them as collaborative team challenges;
  the instructor can disrupt active learners when force-recreating a target to
  reset it. Browser-local mastery XP is motivational self-tracking, not a grade
  or anti-cheat claim.
- Python dependencies are not hash-locked and OS/container vulnerability scans
  are a manual pre-deploy gate, not automated CI. The Caddy build pins its
  source commit, direct security-update modules, toolchain image, and runtime
  image, but digest pins alone still do not solve supply-chain risk.
- NoteVault intentionally retains obsolete dependency pins as a private SCA
  exercise. Its time-bounded exception and containment requirements live in
  `deploy/internal-labs/VULNERABILITY-EXCEPTIONS.md`; no exception applies to
  trusted infrastructure or to a new CRITICAL/cross-boundary finding.
- SQLite/uploads live on an instance root volume. Replacement destroys them
  unless the operator snapshots/exports first. There is no automatic backup,
  retention, restore test, CloudWatch alerting, budget alarm, or HA.
- The bootstrap role remains attached after IMDS is disabled. Its policy can
  only change metadata options on tagged lab instances, but removing the role
  after bootstrap would further reduce standing privilege.
- Terraform state contains rendered cloud-init, infrastructure identifiers,
  public keys, and opaque team IDs. It contains no generated app flags or
  private keys, but it still requires encrypted remote storage and access logs.

Do not widen security groups, enable public SSH, attach the Docker socket to a
lab, join Caddy to lab networks, or replace fixed relays with a request-routed
forward proxy to work around an operational problem.
