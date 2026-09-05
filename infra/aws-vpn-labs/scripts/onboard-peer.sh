#!/usr/bin/env bash
# Run from the connected instructor device. The edge accepts public keys only.
set -euo pipefail

usage() {
  echo "usage: WG_EDGE_SSH_TARGET=ubuntu@10.66.0.1 SSH_IDENTITY_FILE=/path/to/key \\" >&2
  echo "  bash onboard-peer.sh OPAQUE_NAME team1|team2 ADDRESS PUBLIC_KEY_FILE" >&2
  exit 2
}

[ "$#" -eq 4 ] || usage
name=$1
team=$2
address=${3%/32}
public_key_file=$4

[[ "$name" =~ ^[a-z0-9][a-z0-9_-]{1,30}$ ]] || usage
[[ "$team" =~ ^team[12]$ ]] || usage
[[ "$address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || usage
[ -f "$public_key_file" ] || { echo "public key file not found" >&2; exit 1; }
public_key=$(tr -d '\r\n' < "$public_key_file")
[[ "$public_key" =~ ^[A-Za-z0-9+/]{43}=$ ]] || {
  echo "file does not contain exactly one WireGuard public key" >&2
  exit 1
}

edge=${WG_EDGE_SSH_TARGET:-ubuntu@10.66.0.1}
ssh_options=(-o IdentitiesOnly=yes)
if [ -n "${SSH_IDENTITY_FILE:-}" ]; then
  [ -f "$SSH_IDENTITY_FILE" ] || { echo "SSH identity file not found" >&2; exit 1; }
  ssh_options+=(-i "$SSH_IDENTITY_FILE")
fi
ssh "${ssh_options[@]}" "$edge" \
  sudo /usr/local/sbin/wg-peer-admin add "$name" "$team" "$address" "$public_key"

echo "Enrollment is active. Give the peer its assigned team URL; do not collect its private key."
