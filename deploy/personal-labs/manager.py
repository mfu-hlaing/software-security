"""Operator-owned narrow lab manager. Student web containers never get Docker access."""
import json
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time

LABS = {
    'threat': ('software-security-internal-labs-week01:latest', {}, [], '/notes'),
    'injection': ('software-security-internal-labs-week04:latest', {}, [], '/'),
    'xss': ('software-security-internal-labs-week05:latest', {}, [], '/'),
    'auth': ('software-security-internal-labs-week06:latest', {}, [], '/'),
    'project': ('software-security-internal-labs-notevault-team-{team}:latest', {},
                ['python','-c', "import app; app.seed(); app.app.run(host='0.0.0.0',port=5000,debug=False)"], '/'),
    'api-bad': ('software-security-semester-api-vulnerable:latest', {'FLASK_APP':'vulnerable_api'}, [], '/'),
    'api-good': ('software-security-semester-api-defended:latest', {'FLASK_APP':'solution_api'}, [], '/'),
    'ai-bad': ('software-security-semester-ai-vulnerable:latest', {'FLASK_APP':'vulnerable_chatbot'}, [], '/'),
    'ai-good': ('software-security-semester-ai-defended:latest', {'FLASK_APP':'guarded_chatbot'}, [], '/'),
    'ops-bad': ('software-security-semester-ops-vulnerable:latest', {'FLASK_APP':'insecure_service'}, [], '/'),
    'ops-good': ('software-security-semester-ops-defended:latest', {'FLASK_APP':'secure_service'}, [], '/'),
}


def command(args, check=True):
    return subprocess.run(['docker', *args], check=check, capture_output=True, text=True, timeout=30)


def existing(name):
    result = command(['inspect', name], check=False)
    if result.returncode == 0:
        return json.loads(result.stdout)[0]
    if 'No such object' in result.stderr or 'No such container' in result.stderr:
        return None
    raise RuntimeError('Docker status is unavailable')


class Manager:
    def __init__(self, config, state_path):
        self.config, self.path = config, Path(state_path)
        self.lock = threading.RLock()
        self.states = json.loads(self.path.read_text()) if self.path.exists() else {}
        if config['team'] not in (1, 2) or not re.fullmatch(r'team[12]\.labs\.test', config['zone']):
            raise ValueError('invalid team')

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.states))
        tmp.replace(self.path)

    def valid_slot(self, slot):
        return type(slot) is int and str(slot) in self.config['peers']

    def name(self, slot):
        if not self.valid_slot(slot):
            raise ValueError('unknown slot')
        return f'outsiders-p{slot}-app'

    def status(self, slot):
        with self.lock:
            self.name(slot)
            state = self.states.get(str(slot))
            if not state:
                # A crash between container creation and state persistence must not
                # leave an unbounded orphan after a manager restart.
                orphan = existing(self.name(slot))
                if orphan:
                    command(['rm', '-f', self.name(slot)])
            if state and state['expires'] <= time.time():
                self.stop(slot)
                state = None
            if state:
                obj = existing(self.name(slot))
                if not obj or not obj['State']['Running']:
                    self.states.pop(str(slot), None)
                    self.save()
                    state = None
            return {'state': 'running' if state else 'stopped', **(state or {}),
                    'url': f"https://p{slot}.{self.config['zone']}:8443" + (state or {}).get('path', '/'),
                    'lease_minutes': 60}

    def stop(self, slot):
        with self.lock:
            name = self.name(slot)
            removed = command(['rm', '-f', name], check=False)
            if removed.returncode and existing(name):
                raise RuntimeError('The target could not be stopped')
            self.states.pop(str(slot), None)
            self.save()
            return {'state':'stopped'}

    def start(self, slot, lab):
        if not isinstance(lab,str) or lab not in LABS:
            raise ValueError('unknown lab')
        with self.lock:
            name = self.name(slot)
            current = self.status(slot)
            if current['state'] == 'running':
                return {'error':'Stop your current lab before starting another. Stopping discards that target’s changes.', **current}
            image, env, extra, path = LABS[lab]
            image = image.format(team=self.config['team'])
            # Resolve the operator-built tag once. Never pull or accept an image from a request.
            result = command(['image', 'inspect', image])
            image_id = json.loads(result.stdout)[0]['Id']
            if not re.fullmatch(r'sha256:[a-f0-9]{64}', image_id):
                raise ValueError('invalid image digest')
            nonce = secrets.token_hex(12)
            env = {**env, 'FLAG_SQLI':f'FLAG{{{nonce}_sql}}', 'FLAG_CMDI':f'FLAG{{{nonce}_command}}',
                   'FLAG_IDOR':f'FLAG{{{nonce}_object}}', 'FLAG_JWT':f'FLAG{{{nonce}_jwt}}',
                   'TEAM_ID':f'practice-{slot}', 'TEAM_SALT':nonce}
            args = ['run','-d','--pull=never','--name',name, '--hostname','personal-lab',
                    '--label','outsiders.managed=true', '--network',f'outsiders-p{slot}',
                    '--network-alias',f'p{slot}-app','--ip',f'172.31.{slot}.2',
                    '--read-only','--user','10001:10001','--cap-drop','ALL',
                    '--security-opt','no-new-privileges:true','--memory','160m','--memory-swap','160m',
                    '--cpus','0.5','--pids-limit','64','--init',
                    '--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777',
                    '--log-driver','local','--log-opt','max-size=5m','--log-opt','max-file=2']
            if lab == 'injection':
                args += ['--sysctl','net.ipv4.ping_group_range=0 2147483647']
            for key, value in env.items():
                args += ['--env',f'{key}={value}']
            command(['rm','-f',name], check=False)
            command([*args, image_id, *extra])
            state = {'lab':lab,'expires':int(time.time())+3600,'path':path}
            self.states[str(slot)] = state
            self.save()
            return self.status(slot)

    def reap(self):
        with self.lock:
            for slot in self.config['peers']:
                self.status(int(slot))
