#!/usr/bin/env bash
# Run as root on an existing dedicated team host, from the reviewed checkout.
# Private inputs must already be at /etc/outsiders; they never enter Git/state.
set -euo pipefail
cd /opt/software-security
[ "$(id -u)" = 0 ]
[ -f /etc/outsiders/config.json ]
[ -s /etc/outsiders/broker.token ]
[ -s /etc/outsiders/deepseek.key ]
install -d -m 0700 /var/lib/outsiders /var/backups/outsiders
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup="/var/backups/outsiders/$stamp"
install -d -m 0700 "$backup"
legacy=(docker compose --env-file deploy/internal-labs/.env -f deploy/internal-labs/compose.yml)
python3 deploy/personal-labs/generate.py /etc/outsiders/config.json /etc/outsiders
chmod 0644 /etc/outsiders/Caddyfile
chown 10001:10001 /etc/outsiders/broker.token
chmod 0400 /etc/outsiders/broker.token
chmod 0600 /etc/outsiders/deepseek.key /etc/outsiders/config.json
git rev-parse HEAD > "$backup/release.txt"
docker inspect "$("${legacy[@]}" ps -q learning)" --format '{{.Image}}' > "$backup/previous-learning-image.txt"
docker inspect "$("${legacy[@]}" ps -q caddy)" --format '{{.Image}}' > "$backup/previous-gateway-image.txt"

# Build before interrupting the current learning service. No extra cloud nodes.
# The runtime host-input guard also denies DNS from a default build bridge.
# Only reviewed dependency-install build steps use the host network. No lab
# application is executed by these Dockerfiles during the image build.
docker build --network=host -f deploy/internal-labs/images/learning.Dockerfile \
  -t software-security-internal-labs-learning:latest .
for target in api-vulnerable api-defended ai-vulnerable ai-defended ops-vulnerable ops-defended; do
  case "$target" in
    api-*) source_dir=labs/week10-api-security;;
    ai-*) source_dir=labs/week14-ai-llm-security;;
    ops-*) source_dir=labs/week15-devsecops-pipeline;;
  esac
  docker build --network=host --build-arg "LAB_DIR=$source_dir" \
    -f deploy/semester-labs/target.Dockerfile \
    -t "software-security-semester-$target:latest" .
done

# Resolve an active-only manifest. It contains runtime secrets and stays root-only.
python3 - <<'PY'
import json,os,subprocess
from pathlib import Path
args=['docker','compose','--env-file','deploy/internal-labs/.env','-f','deploy/internal-labs/compose.yml',
      '-f','/etc/outsiders/compose.override.json','config','--format','json']
data=json.loads(subprocess.check_output(args))
data['services']={k:v for k,v in data['services'].items() if k in ('learning','caddy','learning-relay') or k.startswith('personal-')}
used={n for s in data['services'].values() for n in s.get('networks',{})}
data['networks']={k:v for k,v in data['networks'].items() if k in used}
p=Path('/etc/outsiders/compose.json');p.write_text(json.dumps(data,indent=2));p.chmod(0o600)
PY

# Validate the gateway syntax before cutover, using its existing trusted image.
docker run --rm --network none --entrypoint caddy \
  -v /etc/outsiders/Caddyfile:/etc/caddy/Caddyfile:ro \
  software-security-internal-labs-caddy:latest validate --config /etc/caddy/Caddyfile

"${legacy[@]}" stop learning caddy
for volume in learning_data caddy_data caddy_config; do
  source=$(docker volume inspect "software-security-internal-labs_$volume" --format '{{.Mountpoint}}')
  tar -C "$source" -czf "$backup/$volume.tar.gz" .
  tar -tzf "$backup/$volume.tar.gz" >/dev/null
done

# Remove only the disposable shared target containers, retaining all named volumes.
team=$(python3 -c 'import json;print(json.load(open("/etc/outsiders/config.json"))["team"])')
old=(week01 week01-relay week04 week04-relay week05 week05-relay week06 week06-relay "notevault-team-$team" "notevault-team-$team-relay")
"${legacy[@]}" stop "${old[@]}"
"${legacy[@]}" rm -f "${old[@]}"
docker compose -f /etc/outsiders/compose.json up -d --wait

install -m 0644 deploy/personal-labs/outsiders-broker.service /etc/systemd/system/outsiders-broker.service
systemctl daemon-reload
systemctl enable --now outsiders-broker.service
systemctl restart outsiders-broker.service
systemctl is-active --quiet outsiders-broker.service
echo "Personal-lab runtime ready for account enrollment and VPN isolation verification. Backup: $backup"
