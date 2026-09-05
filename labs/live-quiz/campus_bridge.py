"""Narrow authenticated protocol to the host's lab/AI service; no Docker socket."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class BridgeUnavailable(Exception):
    pass


def call(action, learner, **fields):
    origin = os.environ.get('CAMPUS_BRIDGE_URL', '')
    parsed = urlsplit(origin)
    if parsed.scheme != 'http' or parsed.hostname not in ('172.30.1.1', '127.0.0.1') or parsed.port != 8787:
        raise BridgeUnavailable('Personal services are not configured on this deployment.')
    try:
        token = Path(os.environ.get('CAMPUS_BRIDGE_TOKEN_FILE', '/run/secrets/campus-bridge-token')).read_text().strip()
        data = json.dumps({'action': action, 'slot': learner['slot'], **fields}).encode()
        req = urllib.request.Request(origin + '/v1/action', data=data, headers={
            'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=40 if action == 'guide' else 20) as response:
            raw = response.read(100001)
        if len(raw) > 100000:
            raise ValueError('oversized response')
        return json.loads(raw)
    except (OSError, ValueError, urllib.error.URLError):
        raise BridgeUnavailable('The service is temporarily unavailable. Your course materials remain available.') from None
