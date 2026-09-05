#!/usr/bin/env bash
# Run this on the student's device. It creates the private key locally and
# prints only the public key that the instructor needs for enrollment.
set -euo pipefail

usage() {
  echo "usage: WIREGUARD_DNS=SERVER_IP LAB_ALLOWED_IPS='VPC_CIDR, WG_CIDR' \\" >&2
  echo "  bash create-peer-config.sh OPAQUE_NAME ADDRESS ENDPOINT SERVER_PUBLIC_KEY" >&2
  echo "example ADDRESS: 10.66.0.10/32; ENDPOINT: 203.0.113.10:51820" >&2
  exit 2
}

[ "$#" -eq 4 ] || usage
name=$1
address=$2
endpoint=$3
server_public_key=$4

[[ "$name" =~ ^[a-z0-9][a-z0-9_-]{1,30}$ ]] || usage
[[ "$address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/32$ ]] || usage
[[ "$endpoint" =~ ^[^[:space:]:]+:[0-9]{4,5}$ ]] || usage
[[ "$server_public_key" =~ ^[A-Za-z0-9+/]{43}=$ ]] || usage
: "${WIREGUARD_DNS:?set WIREGUARD_DNS from terraform output -raw wireguard_dns}"
: "${LAB_ALLOWED_IPS:?set LAB_ALLOWED_IPS from terraform output -raw peer_allowed_ips}"
[[ "$WIREGUARD_DNS" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || usage
[[ "$LAB_ALLOWED_IPS" != *$'\n'* && "$LAB_ALLOWED_IPS" == *,* ]] || usage
command -v wg >/dev/null || { echo "wg is required" >&2; exit 1; }

output_root=${PEER_OUTPUT_DIR:-generated-peers}
output_dir="$output_root/$name"
[ ! -e "$output_dir" ] || {
  echo "$output_dir already exists; refusing to overwrite private material" >&2
  exit 1
}

umask 077
mkdir -p "$output_dir"
wg genkey > "$output_dir/private.key"
wg pubkey < "$output_dir/private.key" > "$output_dir/public.key"

cat > "$output_dir/$name.conf" <<EOF
[Interface]
PrivateKey = $(cat "$output_dir/private.key")
Address = $address
DNS = $WIREGUARD_DNS

[Peer]
PublicKey = $server_public_key
Endpoint = $endpoint
AllowedIPs = $LAB_ALLOWED_IPS
PersistentKeepalive = 25
EOF

chmod 0600 "$output_dir/private.key" "$output_dir/$name.conf"
echo "Private config created at $output_dir/$name.conf"
echo "Give the instructor only this public key:"
cat "$output_dir/public.key"
