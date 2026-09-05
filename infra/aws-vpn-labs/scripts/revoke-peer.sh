#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ] || [[ ! "$1" =~ ^[a-z0-9][a-z0-9_-]{1,30}$ ]]; then
  echo "usage: WG_EDGE_SSH_TARGET=ubuntu@10.66.0.1 bash revoke-peer.sh OPAQUE_NAME" >&2
  exit 2
fi

edge=${WG_EDGE_SSH_TARGET:-ubuntu@10.66.0.1}
ssh -o IdentitiesOnly=yes "$edge" \
  sudo /usr/local/sbin/wg-peer-admin revoke "$1"

echo "Revoked immediately on the edge. Confirm with the peer isolation smoke test."
