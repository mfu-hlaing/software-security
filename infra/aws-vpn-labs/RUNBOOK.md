# Operator runbook

## 1. Preconditions

Use a dedicated AWS training account with MFA, an accountable owner, a budget
alarm, and an agreed shutdown date. Get institutional authorization before
hosting intentionally vulnerable software. Confirm the VPC and WireGuard CIDRs
do not overlap campus/home networks used by the cohort. Compose reserves
`172.30.0.0/16`; confirm it does not collide with host or VPN routes either.

This workspace may contain real credential and WireGuard files **outside** the
repository. Never archive, upload, `docker build`, or run Terraform from the
workspace root. The only deployment source is a reviewed commit of `repo/`;
every Compose build context resolves to that repository and its `.dockerignore`
starts with deny-all. Run `git status --short` and inspect untracked files before
publishing the pinned commit.

The operator needs Terraform 1.6+, AWS CLI credentials, WireGuard tools, and an
instructor SSH key. Resolve and review an Ubuntu 24.04 amd64 AMI in the chosen
Region; do not add a moving “latest” AMI lookup.

Create an encrypted/versioned S3 state bucket and lock table in a separate
administrator bootstrap. Copy `backend.tf.example` to `backend.tf`, fill its
non-secret names, and restrict bucket/table access to the deployment role.

## 2. Prepare public inputs

Generate the instructor's WireGuard key on the instructor device:

```sh
umask 077
wg genkey > instructor-wg.key
wg pubkey < instructor-wg.key > instructor-wg.pub
```

Copy `terraform.tfvars.example` to the ignored `terraform.tfvars`. Replace the
AMI, full 40-character public repository commit SHA, and both instructor public
keys. Use opaque team aliases; maintain any alias-to-person mapping in the
institution's approved roster system, never Git, tags, Terraform, or filenames.

Before deployment, run this from the repository root (the example environment
is used only to resolve Compose build metadata; it is never deployed):

```sh
docker compose --env-file deploy/internal-labs/.env.example \
  -f deploy/internal-labs/compose.yml --profile all-teams \
  build caddy learning-relay
trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --exit-code 1 software-security-internal-labs-caddy:latest
trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
  --exit-code 1 software-security-internal-labs-learning-relay:latest
cd infra/aws-vpn-labs
terraform fmt -check -recursive
terraform init
terraform validate
terraform plan -out pilot.tfplan
terraform show pilot.tfplan
```

The reviewed plan should contain three instances, one EIP, no public address on
either team host, and no public TCP ingress. Apply only that saved plan.

## 3. Bootstrap and build the instructor tunnel

Cloud-init on each private host retries for fifteen minutes because its default
route can exist before edge NAT is operational. Use the commands in
`lab_bootstrap_status_commands` if a host does not become ready.

The edge generates its private key locally; it never enters Terraform state.
Its public key is printed explicitly to the EC2 serial/system console. Obtain
the exact retrieval command with:

```sh
terraform output -raw wireguard_server_public_key_command
```

Run the displayed AWS CLI command and copy only the value after
`WIREGUARD_SERVER_PUBLIC_KEY=`. Then populate `instructor_client_template`:

```sh
terraform output -raw instructor_client_template
```

Insert the instructor private key locally and the retrieved server public key,
save with mode 0600, and connect. Private SSH and edge DNS are tunnel-internal:
the public edge security group needs only outer UDP 51820 because decapsulated
`wg0` SSH/DNS are governed by nftables (`10.66.0.2` instructor SSH; all enrolled
peers DNS).

Check both private hosts' console logs for `IMDS_DISABLED` and
`TEAM_LAB_READY`. Over the instructor tunnel, also verify:

```sh
aws ec2 describe-instances --region REGION --instance-ids LAB_INSTANCE_IDS \
  --query 'Reservations[].Instances[].{Public:PublicIpAddress,IMDS:MetadataOptions.HttpEndpoint}'
```

Expected: `Public` is null and `IMDS` is `disabled` for both lab hosts.

## 4. Trust the private HTTPS roots

Each team host creates a separate Caddy internal CA. Retrieve the appropriate
root only over instructor SSH, verify its fingerprint out-of-band, and install
it only in a managed course browser/profile:

```sh
ssh ubuntu@TEAM_HOST 'cd /opt/software-security/deploy/internal-labs && sudo docker cp "$(sudo docker compose --env-file .env -f compose.yml ps -q caddy)":/data/caddy/pki/authorities/local/root.crt /tmp/team-root.crt && sudo cat /tmp/team-root.crt' > team-root.crt
openssl x509 -in team-root.crt -noout -sha256 -fingerprint
```

Do not ask students to suppress browser warnings for normal use and do not
install these roots into personal system-wide stores when a browser-scoped
trust store is available.

Retrieve each host's separately generated learning-app invite only through the
instructor tunnel and private SSH:

```sh
ssh ubuntu@TEAM_HOST \
  "sudo sed -n 's/^LIVE_QUIZ_INVITE_CODE=//p' /opt/software-security/deploy/internal-labs/.env"
```

Never expose this value in Terraform state, EC2 console output, chat, or the
repository. Give a team's invite to that team only and use it for the team's
one-time learning-app registration.

## 5. Enroll one device per fixed slot

On the student's device, create its private material locally:

```sh
WIREGUARD_DNS="$(terraform output -raw wireguard_dns)" \
LAB_ALLOWED_IPS="$(terraform output -raw peer_allowed_ips)" \
bash scripts/create-peer-config.sh \
  peer-a7 10.66.0.10/32 \
  "$(terraform output -raw wireguard_public_endpoint)" SERVER_PUBLIC_KEY
```

The explicit Terraform outputs keep custom VPC and WireGuard CIDRs in sync;
the helper intentionally has no baked-in network defaults.

The student gives the instructor only `generated-peers/peer-a7/public.key`.
From the already connected instructor device:

```sh
WG_EDGE_SSH_TARGET=ubuntu@10.66.0.1 \
  bash scripts/onboard-peer.sh peer-a7 team1 10.66.0.10/32 /path/to/public.key
```

Never accept or escrow a client private key. Never reuse a peer config between
friends or devices. Test from that team peer—not the instructor, who is allowed
to both hosts:

```sh
bash scripts/smoke-peer-isolation.sh \
  https://learn.team1.labs.test:8443 \
  https://learn.team2.labs.test:8443
```

The assigned URL must load and the other team must time out/fail. Run the host
test against each node as instructor:

```sh
bash scripts/smoke-host-isolation.sh ubuntu@10.60.10.10 10.60.10.10
bash scripts/smoke-host-isolation.sh ubuntu@10.60.20.10 10.60.20.10
```

Do not onboard anyone if a negative test unexpectedly succeeds.

## 6. Revoke, operate, reset

Revoke a lost device or departing participant immediately:

```sh
WG_EDGE_SSH_TARGET=ubuntu@10.66.0.1 bash scripts/revoke-peer.sh peer-a7
```

Reset a team's disposable exercise state without deleting learning accounts,
submissions, the learning database, or the Caddy CA:

```sh
bash scripts/reset-team-target.sh ubuntu@10.60.10.10 week05
# accepted targets: week01, week04, week05, week06, project, all
```

This is an instructor action and disrupts anyone currently using that target.
The command force-recreates only the allowlisted application container; its
fixed relay and shared Caddy ingress stay up. Run the matching positive/negative
smoke checks after a reset if the host is being returned to the cohort.

Keep the edge patched. Stop the two lab instances outside teaching hours to
reduce compute cost; EBS and public IPv4 charges continue. Stopping the edge
disconnects everyone and its EIP remains billable. This pilot uses a NAT
instance instead of a NAT Gateway to reduce steady cost, accepting a single
point of failure and lower throughput.
Both instance types use standard (not unlimited) T3 CPU credits, preferring
predictable throttling to surprise surplus-credit charges.

The active single-team stack declares about 1.7 GiB of container memory limits
on a 2 GiB `t3.small`; those limits are ceilings, not a reservation, and leave
little room for Docker and the OS. During every pilot session monitor
`docker stats`, `free -h`, and kernel OOM events (`journalctl -k | grep -i oom`).
Use `t3.medium` before increasing cohort/concurrency or if memory pressure or
OOM kills appear. Image builds are serialized only to make initial bootstrap
less bursty; that is not a capacity guarantee.

The edge's WireGuard private key and enrolled-peer database exist only on its
root volume. Replacing the edge destroys both. Treat an edge replacement as a
key rotation: retrieve and verify the new server public key, re-enroll every
client public key into its original fixed slot, and securely reissue/update all
client configs with the new server public key and endpoint before reopening the
labs. Do not copy the old server private key into Terraform or cloud-init.

Changing `repository_ref` replaces team instances because bootstrap is
immutable. Export the learning database/uploads or create encrypted snapshots
and restore-test them before replacement. To reset only disposable target state,
restart those containers; deleting Compose volumes also deletes learning data
and the Caddy CA, so it requires an explicit backup and planned client CA update.

At term end: revoke all peers, export only required course records under the
institution retention policy, destroy the Terraform stack, confirm EIPs and
volumes are gone, delete locally generated peer configs securely, and remove
the course CA roots from client profiles.
