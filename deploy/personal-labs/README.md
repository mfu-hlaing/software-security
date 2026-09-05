# Outsiders personal security academy

This release adds individual practice identities and on-demand isolated targets to the existing private AWS course deployment. `/campus` is the academy entrance, `/campus/architecture` explains the system and computes operating cost, and `/campus/week/1` through `/campus/week/19` provide worked cases, visual sequences, six-slide explanations, practical tasks, advanced prompts and source links.

## Runtime and trust

The original Terraform owns one WireGuard/NAT edge and two private team EC2 hosts. No additional EC2 instance, public listener, load balancer or NAT Gateway is required. The five-person deployment uses three learner slots on one team host and two on the other. Each learner gets a separate account, unique password, VPN /32, target hostname and internal target network. Student IDs are usernames, never passwords. The 57 self-reported checkpoints are saved per learner and remain separate from grades; the original browser-local pathway is retained as a companion. Roster and key files are outside Git and Terraform state.

The learning service, its fixed relay and Caddy retain their existing named volumes and private CA. The ten disposable shared target/relay containers on each host are replaced by two or three fixed personal relays. A trusted host service accepts only start, stop, status and guide requests from the learning container. Its token is not the DeepSeek key. The learning image gets only the bridge token; the API key stays in a separate host-only file. The browser receives neither. Every personal hostname checks the direct WireGuard peer IP at Caddy; Caddy overwrites the application’s peer header. Application sessions also require the account’s assigned peer.

The host manager chooses from eleven reviewed images. Requests cannot select a command, mount, image, hostname, subnet or Docker option. Target containers have 160 MiB, 0.5 CPU, 64 PIDs, no capabilities, no host ports, non-root UID 10001 and a read-only root. A 64-MiB tmpfs holds disposable changes. Fixed relays have 32 MiB and connect only their target network and trusted ingress. New outbound target connections are blocked outside their subnet, including the host and metadata. These containers share a kernel; this is not a kernel-exploitation lab.

One target per learner is allowed at a time. Stopping or expiring a target destroys only its disposable state. A 60-minute lease is enforced by a host reaper every 30 seconds, including after restart. Orphan containers are removed on reconciliation. Learning accounts, worksheets, submissions and the private CA remain on persistent storage.

## Scout and source grounding

Scout calls DeepSeek V4 Flash in non-thinking mode at the fixed HTTPS API endpoint. It receives the selected week’s authored explanation, public lecture/README excerpts and a question capped at 1500 characters. It does not receive roster data, grades, uploaded evidence, instructor files, API keys or lab credentials. Basic credential/ID/email patterns are removed from questions; this is not a universal DLP guarantee, so the UI tells learners not to paste private information.

The model has no tools. Citations must refer to server-selected source IDs; links are returned by the server and rendered as text and allowlisted internal links. Unknown citations and malformed responses do not become invented resource links. Current implementation notes take precedence over legacy lecture commands. A reviewed Week 10 hint replaces known misleading claims about forged identity headers or localhost commands in the personal runtime. AI explanations can still be wrong; learners must compare the linked source.

Questions and answers are not stored by this platform. Only rate-limit and reserved-spend counters persist. Sending a question sends it to DeepSeek; the provider’s own data handling still applies. The platform’s default guard reserves $0.011 for each attempted request, at most $1/day and $5/month per host, with 30 questions/day per learner and one in-flight provider call per host. Reservations intentionally overestimate usage and are not a bill. No automatic top-up is performed. Other uses of the supplied key are outside this application’s cap. Recheck provider prices before changing the model or increasing the byte/output limits.

## Reproducible deployment

Use the established instructor VPN and private SSH. No public SSH or web port needs to be added.

1. Checkout the tested release in `/opt/software-security`. Keep the bootstrap Terraform ref unchanged during an in-place application upgrade; changing it replaces team instances and needs a separate backup/restore plan.
2. Install private inputs in `/etc/outsiders`: `config.json`, `broker.token`, `deepseek.key`. The token must have at least 32 random characters. The API key file is root-owned mode 0600. Never place these values in image build arguments, Git or Terraform state.
3. A team configuration has `team` (1 or 2), `zone` (`team1.labs.test` or `team2.labs.test`), `peers` (slot strings 1–3 to that team’s existing fixed WireGuard IPv4 slots), `token_file` (`/etc/outsiders/broker.token`), and `deepseek_key_file` (`/etc/outsiders/deepseek.key`). It contains no student IDs or names.
4. Run `sudo bash deploy/personal-labs/install.sh`. It builds first, resolves a root-only active-service manifest, validates Caddy, briefly stops learning/gateway for consistent volume backups, removes only disposable shared target containers, starts the active manifest and installs the host guard and broker.
5. Enroll only the authorized roster into a separate database. Use `LEARNER_DB_PATH` pointing to `learners.db` inside the learning volume and `python3 deploy/personal-labs/enroll.py PRIVATE_ROSTER PRIVATE_DELIVERY_DIRECTORY`. Set database ownership to UID/GID 10001 and mode 0600. Each roster row contains exact `student_id`, `name`, `slot`, `vpn_ip`, `login_url`. The CLI writes a separate mode-0600 credential file per learner; never distribute the whole directory to the group.
6. Enroll a unique public WireGuard key in each assigned /32 using the existing operator helper. Keep client private keys only in their protected device/onboarding files, never on the AWS edge. Share each learner’s own profile, password and public course CA privately.
7. Verify from actual team peers: own login succeeds, wrong password and wrong assigned peer fail, own target succeeds, another student’s hostname returns 403, cross-team access fails, and supplied forwarding headers cannot override identity. Test clean/reset/expiry and all eleven target types. Check real source-linked AI output and quota/error fallback. Finish with the host/metadata/Internet negative tests.

Operate this deployment with `sudo docker compose -f /etc/outsiders/compose.json ...`; running the old full manifest’s `up` can recreate the retired shared targets and exceed capacity. After recreating the learning container, restart `outsiders-broker.service` to refresh the exact-IP firewall allowance. Docker restarts also restart this service. Use `systemctl status outsiders-broker` and sanitized status summaries; do not dump environment values, secret-bearing resolved Compose JSON or private onboarding files into chat.

## Cost and capacity

Singapore public list prices checked 2026-09-05: t3.micro $0.0132/hour, t3.small $0.0264/hour, gp3 $0.096/GiB-month; one public IPv4 $0.005/hour. The current three hosts each have 24 GiB encrypted gp3. At 730 hours/month: compute $48.18 + storage $6.912 + IPv4 $3.65 = **$58.742/month**, before tax, snapshots and chargeable traffic. The application’s two AI budgets reserve at most another **$10/month** at the checked model pricing. No EC2 resizing is included in this release.

At 176 hours/month for the two team hosts while leaving the edge on, the same calculation is approximately **$29.49/month** before AI and exclusions. Scheduling is an operator decision, not activated by the interactive calculator. Stopped compute still retains paid storage and the allocated IPv4 remains billable.

The three-slot host has 1424 MiB of declared service ceilings including a 160-MiB host broker; the two-slot host has 1232 MiB. The observed instances expose approximately 1906 MiB, leaving room for Docker and the OS. These figures are a resource envelope, not a classroom load guarantee. Standard T3 credits can throttle sustained CPU load. Keep fuzzers and scanners local; monitor actual CPU, memory, disk and OOM events before expanding beyond five people.

Prices: [AWS EC2](https://aws.amazon.com/ec2/pricing/on-demand/), [regional EC2 price catalog](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-southeast-1/index.csv), [EBS](https://aws.amazon.com/ebs/pricing/), [IPv4](https://aws.amazon.com/vpc/pricing/), [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/).

The personal installer also rebuilds NoteVault from the selected application checkout. Existing running targets retain their current image until they stop. For demo-state preservation during an upgrade, verify a consistent SQLite backup through the running target before stopping it; abort the upgrade on any backup failure. Target storage remains disposable during ordinary use.

## Rollback and account lifecycle

The installer records prior learning/gateway image IDs and consistent learning/CA volume archives under `/var/backups/outsiders/TIMESTAMP/`, readable only by root. To roll back, stop the broker and each exact `outsiders-pN-app`, stop/remove the personal relay containers, retag the recorded previous images, and start the legacy Compose service set. Keep the existing data and CA volumes. Restore an archive only if data restoration is needed; verify it before overwriting a volume. Do not use `down -v`.

Revoke an account by setting its `active` field to 0, stopping its exact personal slot, and revoking its VPN peer through the established helper. Session identity is checked against the active account on every protected request. Changing a password invalidates previous practice sessions. Password reset is an operator action: update only that learner’s salted hash and deliver the new random credential privately. A changed VPN address requires updating the private slot map and the learner row together, regenerating/reloading the gateway and rerunning own/other-peer tests. Never reassign an occupied slot while its previous owner can still authenticate to the VPN.
