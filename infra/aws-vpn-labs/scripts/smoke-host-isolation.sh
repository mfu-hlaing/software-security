#!/usr/bin/env bash
# Run from the connected instructor device after both hosts report ready.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: bash smoke-host-isolation.sh SSH_TARGET HOST_PRIVATE_IP" >&2
  echo "example: bash smoke-host-isolation.sh ubuntu@10.60.10.10 10.60.10.10" >&2
  exit 2
fi

ssh_target=$1
host_private_ip=$2

ssh -o IdentitiesOnly=yes "$ssh_target" sudo bash -s -- "$host_private_ip" <<'REMOTE'
set -euo pipefail
host_private_ip=$1
cd /opt/software-security/deploy/internal-labs
profile=$(sed -n 's/^COMPOSE_PROFILES=//p' .env)
compose=(docker compose --env-file .env -f compose.yml --profile "$profile")

"${compose[@]}" config --quiet
services=(
  caddy learning learning-relay week01 week01-relay week04 week04-relay
  week05 week05-relay week06 week06-relay
)
if [ "$profile" = team1 ]; then
  services+=(notevault-team-1 notevault-team-1-relay)
else
  services+=(notevault-team-2 notevault-team-2-relay)
fi

for service in "${services[@]}"; do
  id=$("${compose[@]}" ps -q "$service")
  [ -n "$id" ] || { echo "FAIL: $service is not running" >&2; exit 1; }
  [ "$(docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' "$id")" = true ] || {
    echo "FAIL: $service root filesystem is writable" >&2; exit 1;
  }
  docker inspect -f '{{json .HostConfig.CapDrop}}' "$id" | grep -q 'ALL' || {
    echo "FAIL: $service does not drop all capabilities" >&2; exit 1;
  }
  docker inspect -f '{{json .HostConfig.SecurityOpt}}' "$id" | grep -q 'no-new-privileges' || {
    echo "FAIL: $service lacks no-new-privileges" >&2; exit 1;
  }
done

# Only Caddy may have a host port. Flask, NoteVault, and relays have none.
for service in learning week01 week04 week05 week06 \
  learning-relay week01-relay week04-relay week05-relay week06-relay; do
  id=$("${compose[@]}" ps -q "$service")
  [ "$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$id")" = '{}' ] || {
    echo "FAIL: $service has a host port" >&2; exit 1;
  }
done
if [ "$profile" = team1 ]; then project=notevault-team-1; else project=notevault-team-2; fi
for service in "$project" "$project-relay"; do
  id=$("${compose[@]}" ps -q "$service")
  [ "$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$id")" = '{}' ] || {
    echo "FAIL: $service has a host port" >&2; exit 1;
  }
done
caddy_id=$("${compose[@]}" ps -q caddy)
[ "$(docker inspect -f '{{(index .HostConfig.PortBindings "8443/tcp" 0).HostPort}}' "$caddy_id")" = 8443 ] || {
  echo "FAIL: Caddy is not the TCP 8443 publisher" >&2; exit 1;
}
ss -lnt | grep -Eq '(^|[[:space:]])(0\.0\.0\.0|\*):8443[[:space:]]' || {
  echo "FAIL: Caddy is not listening on private-host TCP 8443" >&2; exit 1;
}

# Each app has one internal bridge, each relay has that bridge plus ingress,
# and shared Caddy has ingress only.
for service in learning week01 week04 week05 week06; do
  id=$("${compose[@]}" ps -q "$service")
  count=$(docker inspect -f '{{len .NetworkSettings.Networks}}' "$id")
  [ "$count" -eq 1 ] || { echo "FAIL: $service joins $count networks" >&2; exit 1; }
done
[ "$(docker inspect -f '{{len .NetworkSettings.Networks}}' "$caddy_id")" -eq 1 ]
for service in learning-relay week01-relay week04-relay week05-relay week06-relay; do
  id=$("${compose[@]}" ps -q "$service")
  [ "$(docker inspect -f '{{len .NetworkSettings.Networks}}' "$id")" -eq 2 ] || {
    echo "FAIL: $service does not have exactly app+ingress networks" >&2; exit 1;
  }
done
networks=(learning_net week01_net week04_net week05_net week06_net "${profile}_net")
for network in "${networks[@]}"; do
  docker network inspect "software-security-internal-labs_$network" \
    -f '{{.Internal}}' | grep -qx true || {
      echo "FAIL: $network is not internal" >&2; exit 1;
    }
done
docker network inspect software-security-internal-labs_ingress_net \
  -f '{{.Internal}}' | grep -qx false

# Preserve the Week 4 ping theory/lab while retaining cap_drop=ALL.
"${compose[@]}" exec -T week04 ping -c 1 -W 1 127.0.0.1 >/dev/null

# Week 4 may reach its own fixed relay, and a forged Host still returns Week 4.
# It must not resolve ingress peers/other labs or reach the Internet/host.
week04_id=$("${compose[@]}" ps -q week04)
gateway=$(docker network inspect software-security-internal-labs_week04_net \
  -f '{{(index .IPAM.Config 0).Gateway}}')
docker exec "$week04_id" python -c \
  'import urllib.request; r=urllib.request.Request("http://week04-relay:8080/", headers={"Host":"learn.team1.labs.test"}); assert b"Week 4" in urllib.request.urlopen(r, timeout=3).read()'
if docker exec "$week04_id" python -c \
  'import socket; socket.getaddrinfo("learning-relay", 8080)' >/dev/null 2>&1; then
  echo "FAIL: week04 can resolve an ingress-only relay" >&2
  exit 1
fi
for target in "1.1.1.1:443" "$gateway:8443" "$host_private_ip:8443"; do
  if docker exec "$week04_id" python -c \
    'import socket,sys; h,p=sys.argv[1].rsplit(":",1); socket.create_connection((h,int(p)),2)' "$target" \
    >/dev/null 2>&1; then
    echo "FAIL: week04 reached $target" >&2
    exit 1
  fi
done

# The non-internal ingress bridge exists only so Docker can publish 8443.
# Prove that the host DOCKER-USER guard also contains its trusted components:
# shared Caddy (ingress only) and a dual-homed relay must have neither Internet
# nor IMDS access. Requiring nc prevents a missing probe utility from looking
# like a successful negative test.
for service in caddy week04-relay; do
  id=$("${compose[@]}" ps -q "$service")
  docker exec "$id" sh -c 'command -v nc >/dev/null' || {
    echo "FAIL: $service lacks the required network probe" >&2
    exit 1
  }
  for target in 1.1.1.1:443 169.254.169.254:80; do
    if docker exec "$id" sh -c \
      'host=${1%:*}; port=${1##*:}; nc -z -w 2 "$host" "$port"' sh "$target" \
      >/dev/null 2>&1; then
      echo "FAIL: $service reached $target despite LAB-CONTAINER-GUARD" >&2
      exit 1
    fi
  done
done

# Weeks 2/3 stay in first-party browser labs and never link to a shared shell.
learning_id=$("${compose[@]}" ps -q learning)
learning_env=$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$learning_id")
grep -q '^MASTERY_WEEK02_LAB_URL=https://.*/sim/fuzz-verdict$' <<<"$learning_env"
grep -q '^MASTERY_WEEK03_LAB_URL=https://.*/sim/aes-modes$' <<<"$learning_env"

echo "PASS: host hardening, app/relay/ingress egress guards, Week 4 ping, mastery links, and container isolation"
REMOTE
