"""Verify the shell wrapper validates inputs and delegates an exact policy."""
import os
from pathlib import Path
import subprocess
import pytest
SCRIPT=Path(__file__).resolve().parents[2]/'week12-supply-chain/verify-release.sh'
DIGEST='registry.example.test/team/app@sha256:'+'a'*64
@pytest.mark.parametrize('artifact',["app:latest",'local@sha256:'+'a'*64,'-flag',DIGEST+'\n'])
def test_rejects_ambiguous_artifact(artifact):
    p=subprocess.run(['bash',str(SCRIPT),artifact,'expected-identity','https://issuer.example'],capture_output=True)
    assert p.returncode==2

def test_passes_exact_identity_and_issuer(tmp_path):
    fake=tmp_path/'cosign'
    fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n');fake.chmod(0o755)
    p=subprocess.run(['bash',str(SCRIPT),DIGEST,'expected-identity','https://issuer.example'],capture_output=True,text=True,env={**os.environ,'PATH':str(tmp_path)+':'+os.environ['PATH']})
    assert p.returncode==0
    assert p.stdout.splitlines()==['verify','--certificate-identity','expected-identity','--certificate-oidc-issuer','https://issuer.example',DIGEST]
