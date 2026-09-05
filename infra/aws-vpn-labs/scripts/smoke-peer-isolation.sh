#!/usr/bin/env bash
# Run while connected as a TEAM peer, never as the instructor (the instructor is
# intentionally allowed to both hosts).
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: bash smoke-peer-isolation.sh OWN_LEARNING_URL OTHER_TEAM_LEARNING_URL" >&2
  echo "example: ... https://learn.team1.labs.test:8443 https://learn.team2.labs.test:8443" >&2
  exit 2
fi

own_url=$1
other_url=$2
curl_common=(-k -f -sS --connect-timeout 3 --max-time 8 -o /dev/null)

echo "checking assigned host: $own_url"
curl "${curl_common[@]}" "$own_url"

echo "checking cross-team denial: $other_url"
if curl "${curl_common[@]}" "$other_url" 2>/dev/null; then
  echo "FAIL: the other team's HTTPS endpoint was reachable" >&2
  exit 1
fi

echo "PASS: assigned HTTPS is reachable and cross-team HTTPS is denied"
