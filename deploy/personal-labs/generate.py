"""Generate fixed gateway/relay configuration from an operator-owned VPN slot map."""
import argparse
import ipaddress
import json
from pathlib import Path


def generate(config, destination):
    team = config['team']
    if team not in (1, 2) or config['zone'] != f'team{team}.labs.test':
        raise ValueError('Unexpected team DNS zone')
    peers = config['peers']
    if not isinstance(peers, dict) or not 1 <= len(peers) <= 3:
        raise ValueError('The 2 GiB pilot supports at most three allocated personal slots per host.')
    seen = set()
    for slot, peer in peers.items():
        if slot not in ('1','2','3') or peer in seen:
            raise ValueError('Invalid or repeated slot/address')
        ip = ipaddress.IPv4Address(peer)
        allowed = {f'10.66.0.{n}' for n in (range(10,14) if team == 1 else range(20,24))}
        if str(ip) not in allowed:
            raise ValueError('Peer must be in this team’s established fixed WireGuard slots.')
        seen.add(peer)
    zone = config['zone']
    learn = f'learn.{zone}'
    caddy = '''{
 admin off
 auto_https disable_redirects
 https_port 8443
 skip_install_trust
}
(private) {
 tls internal
 header -Server
}
'''
    caddy += f'''https://{learn} {{
 import private
 reverse_proxy learning-relay:8080 {{
  header_up X-Campus-Peer {{remote_host}}
 }}
}}
'''
    for legacy in ('w1','w4','w5','w6','project'):
        caddy += f'''https://{legacy}.{zone} {{
 import private
 redir https://{learn}:8443/campus/dashboard 302
}}
'''
    services = {
        'caddy': {'volumes':['/etc/outsiders/Caddyfile:/etc/caddy/Caddyfile:ro']},
        'learning': {'environment': {
            'LEARNER_REQUIRE_VPN':'1', 'LEARNER_DB_PATH':'/data/learners.db',
            'CAMPUS_BRIDGE_URL':'http://172.30.1.1:8787',
            'CAMPUS_BRIDGE_TOKEN_FILE':'/run/secrets/campus-bridge-token'},
            'volumes':['/etc/outsiders/broker.token:/run/secrets/campus-bridge-token:ro']},
    }
    networks = {}
    for slot, peer in peers.items():
        caddy += f'''https://p{slot}.{zone} {{
 import private
 @owner remote_ip {peer}
 handle @owner {{
  reverse_proxy personal-{slot}-relay:8080 {{
   # Legacy Flask apps may absolutize redirects using the fixed relay Host.
   # Return only this slot's internal origin to a same-origin relative path.
   header_down Location "^https?://p{slot}-app:5000(/.*)$" "$1"
  }}
 }}
 handle {{
  respond "This personal workspace belongs to another VPN identity." 403
 }}
}}
'''
        name = f'personal_{slot}_net'
        services[f'personal-{slot}-relay'] = {
            'image':'software-security-internal-labs-learning-relay:latest',
            'restart':'unless-stopped','read_only':True,'user':'10001:10001',
            'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
            'mem_limit':'32m','cpus':0.15,'pids_limit':48,
            'environment':{'UPSTREAM':f'p{slot}-app:5000'},
            'tmpfs':['/tmp:rw,noexec,nosuid,nodev,size=8m,mode=1777',
                     '/data:rw,noexec,nosuid,nodev,size=8m,mode=0700,uid=10001,gid=10001',
                     '/config:rw,noexec,nosuid,nodev,size=4m,mode=0700,uid=10001,gid=10001'],
            'networks':{'ingress_net':{},name:{'ipv4_address':f'172.31.{slot}.3'}},
            'healthcheck':{'test':['CMD','caddy','validate','--config','/etc/caddy/Caddyfile'],
                           'interval':'30s','timeout':'5s','retries':3},
            'logging':{'driver':'local','options':{'max-size':'5m','max-file':'2'}},
        }
        networks[name] = {'name':f'outsiders-p{slot}','internal':True,
                          'ipam':{'config':[{'subnet':f'172.31.{slot}.0/24'}]}}
    destination.mkdir(parents=True, exist_ok=True)
    (destination/'Caddyfile').write_text(caddy)
    (destination/'compose.override.json').write_text(json.dumps({'services':services,'networks':networks},indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config',type=Path)
    parser.add_argument('destination',type=Path)
    args = parser.parse_args()
    generate(json.loads(args.config.read_text()), args.destination)
