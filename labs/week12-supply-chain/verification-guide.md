# Verify the release you actually intend to trust

The original `sign.sh` is a teaching scaffold. Its wildcard identity/issuer filters do not restrict the signer to your team, and a local Docker image tag is not a registry artifact ready for keyless signing. This supplement makes those requirements explicit.

## Before starting

Use your own registry repository with push access, an installed Cosign CLI, and an artifact already pushed by an authorized build. Keyless signing requires an OIDC flow and may publish identity information in the transparency log. Use course-approved demo identities and non-sensitive artifacts. There is no registry or OIDC account inside the shared browser lab.

## Trace the flow

Source revision → built image → pushed registry digest → keyless signature → expected identity/issuer check → deployment of that exact digest.

The identity is the certificate's exact subject identity (for example, a specific workflow URI). The issuer identifies the expected OIDC provider. Obtain both from your intended signing setup, not from whatever identity an untrusted artifact happens to present.

## Practice commands

Run from `labs/week12-supply-chain` in your own checkout. Replace the three values with real values from your own authorized signing setup; angle-bracket text is not an executable command.

```bash
# Supply an actual registry/repository@sha256:<64 lowercase hex digits>.
export RELEASE_IMAGE='your registry artifact pinned by digest'
export EXPECTED_IDENTITY='your exact approved signer identity'
export EXPECTED_ISSUER='your exact approved OIDC issuer'

# Signing mutates your registry and uses your OIDC identity. Only do this for
# the demo artifact you intentionally chose to publish and sign.
cosign sign "$RELEASE_IMAGE"

# Read-only verification: should pass only for the intended artifact/identity.
bash verify-release.sh "$RELEASE_IMAGE" "$EXPECTED_IDENTITY" "$EXPECTED_ISSUER"

# Negative policy test: a different signer identity must not be accepted.
if bash verify-release.sh "$RELEASE_IMAGE" 'deliberately-wrong-identity' "$EXPECTED_ISSUER"; then
  echo 'FAIL: unexpected signer accepted'
else
  echo 'Expected rejection; inspect the diagnostic to confirm identity mismatch'
fi
```

A failed network connection is not a successful identity-rejection test. Preserve the error category. Separately test a deliberately unsigned artifact that you control; do not assume a public image is unsigned. For tampering, compare a separately built altered artifact digest rather than editing a signed artifact and continuing to refer to the old digest.

## What to explain

- Why a valid signature from the wrong identity fails your release policy.
- Why an SBOM is inventory, not proof of a vulnerability-free artifact.
- Why provenance needs to bind the source/build inputs to the same subject digest.
- Which SLSA build requirements you actually evidenced; a signature alone does not establish a level.

References: [Sigstore verification](https://docs.sigstore.dev/cosign/verifying/verify/), [SLSA 1.2](https://slsa.dev/spec/v1.2/).
