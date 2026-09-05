#!/usr/bin/env bash
# Read-only verification of a registry artifact against an explicit keyless identity.
set -euo pipefail
if [[ $# -ne 3 ]]; then
  echo 'Usage: bash verify-release.sh REGISTRY/REPOSITORY@sha256:DIGEST EXPECTED_IDENTITY EXPECTED_ISSUER' >&2
  exit 2
fi
artifact=$1
identity=$2
issuer=$3
if [[ ! "$artifact" =~ ^[A-Za-z0-9][A-Za-z0-9._:/-]*@sha256:[a-f0-9]{64}$ ]] || [[ "$artifact" != */* ]]; then
  echo 'Use a registry repository pinned to a complete lowercase sha256 digest, not a local image tag.' >&2
  exit 2
fi
if [[ -z "$identity" || -z "$issuer" || "$identity" == *'*'* || "$issuer" == *'*'* ]]; then
  echo 'Expected signer and OIDC issuer must be explicit, nonempty identities without wildcard matching.' >&2
  exit 2
fi
command -v cosign >/dev/null || { echo 'Install Cosign in your local tool environment first.' >&2; exit 127; }
exec cosign verify --certificate-identity "$identity" --certificate-oidc-issuer "$issuer" "$artifact"
