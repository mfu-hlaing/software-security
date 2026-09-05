#!/usr/bin/env bash
# Instructor-only reset for disposable team targets. The learning database,
# submissions, accounts, and Caddy CA are deliberately outside this command.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: bash reset-team-target.sh SSH_TARGET week01|week04|week05|week06|project|all" >&2
  echo "example: bash reset-team-target.sh ubuntu@10.60.10.10 week05" >&2
  exit 2
fi

ssh_target=$1
target=$2
case "$target" in
  week01|week04|week05|week06|project|all) ;;
  *) echo "unknown disposable target: $target" >&2; exit 2 ;;
esac

ssh -o IdentitiesOnly=yes "$ssh_target" sudo bash -s -- "$target" <<'REMOTE'
set -euo pipefail
target=$1
cd /opt/software-security/deploy/internal-labs
profile=$(sed -n 's/^COMPOSE_PROFILES=//p' .env)
case "$profile" in
  team1|team2) ;;
  *) echo "invalid host profile" >&2; exit 1 ;;
esac

compose=(docker compose --env-file .env -f compose.yml --profile "$profile")
project_service="notevault-team-${profile#team}"
case "$target" in
  week01) services=(week01) ;;
  week04) services=(week04) ;;
  week05) services=(week05) ;;
  week06) services=(week06) ;;
  project) services=("$project_service") ;;
  all) services=(week01 week04 week05 week06 "$project_service") ;;
esac

for service in "${services[@]}"; do
  "${compose[@]}" up -d --force-recreate --no-deps "$service"
  id=$("${compose[@]}" ps -q "$service")
  [ -n "$id" ] || { echo "reset failed: $service did not start" >&2; exit 1; }
  attempts=0
  until [ "$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$id")" = healthy ]; do
    attempts=$((attempts + 1))
    [ "$attempts" -lt 60 ] || {
      docker inspect -f '{{json .State}}' "$id" >&2
      echo "reset failed: $service did not become healthy" >&2
      exit 1
    }
    sleep 1
  done
  echo "reset complete: $service"
done
REMOTE

echo "Only disposable target state was recreated; learning accounts, progress, submissions, and the private CA were preserved."
