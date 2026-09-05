"""Exercise this LOCAL release over verified TLS and inspect its isolation contract.

No TLS bypass, real account, flag capture, cloud mutation or load test. Rerunning
creates only disposable demo users in the isolated API targets.
"""
from pathlib import Path
import json
import re
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
COMPOSE=['docker','compose','--env-file',str(HERE/'.env'),'-f',str(HERE/'compose.json')]

def run(args,**kwargs):
    return subprocess.run(args,check=True,capture_output=True,text=True,**kwargs).stdout

def main():
    config=json.loads(run(COMPOSE+['config','--format','json']))
    gateway=config['services']['gateway']
    port=str(gateway['ports'][0]['published'])
    assert gateway['ports'][0]['host_ip']=='127.0.0.1', 'This script is specifically for the loopback development deployment.'
    env=gateway['environment']; ca=HERE/'root.crt'
    run(COMPOSE+['cp','gateway:/data/caddy/pki/authorities/local/root.crt',str(ca)])
    checks=[]
    def request(host,path='/',expected=200,headers=(),body=None):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'body'
            args=['curl','--silent','--show-error','--noproxy','*','--cacert',str(ca),
                  '--resolve',f'{host}:{port}:127.0.0.1','--max-time','8',
                  '-o',str(out),'-w','%{http_code}',f'https://{host}:{port}{path}']
            for header in headers: args+=['-H',header]
            if body is not None: args+=['-H','Content-Type: application/json','--data',json.dumps(body)]
            code=int(run(args)); data=out.read_text(errors="replace")
            assert code==expected,(host,path,code,expected)
            checks.append({'host':host,'path':path,'status':code})
            return data
    learn=env['SEMESTER_LEARN_HOST']
    request(learn,'/learn/software-security/journey')
    links=set()
    for n in range(1,20):
        body=request(learn,f'/learn/software-security/journey/week/{n}')
        assert 'data-checkpoint="defend"' in body
        assert '?v=' in body
        links.update(href.replace('&amp;','&') for href in re.findall(r'href="([^"]+)"',body) if href.startswith(('/learn/','/sim/','/static/')))
    for link in sorted(links): request(learn,link)
    bad=env['SEMESTER_API_VULNERABLE_HOST']; good=env['SEMESTER_API_DEFENDED_HOST']
    request(bad,'/api/users/3/orders')
    request(good,'/api/users/3/orders',401)
    request(good,'/api/users/3/orders',403,['X-User-Id: 1'])
    request(good,'/api/users/1/orders',200,['X-User-Id: 1'])
    payload={'username':'semester-smoke','password':'demo-only','is_admin':True,'balance':42}
    assert json.loads(request(bad,'/api/users',201,body=payload))['is_admin'] is True
    defended=json.loads(request(good,'/api/users',201,body=payload))
    assert defended['is_admin'] is False and defended['balance']==0
    for variant in ('VULNERABLE','DEFENDED'):
        host=env[f'SEMESTER_AI_{variant}_HOST']
        assert 'Hello' in request(host,'/?msg=hello')
    host=env['SEMESTER_AI_DEFENDED_HOST']
    html=request(host,'/?msg=%3Cscript%3Ealert(1)%3C%2Fscript%3E')
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    request(env['SEMESTER_OPS_VULNERABLE_HOST'],'/admin',200)
    request(env['SEMESTER_OPS_DEFENDED_HOST'],'/admin',403)
    request(env['SEMESTER_OPS_DEFENDED_HOST'],'/admin',403,['Authorization: bob-token'])
    request(env['SEMESTER_OPS_DEFENDED_HOST'],'/admin',200,['Authorization: alice-token'])
    apps=['learning','api-vulnerable','api-defended','ai-vulnerable','ai-defended','ops-vulnerable','ops-defended']
    for name in config['services']:
        container=run(COMPOSE+['ps','-q',name]).strip(); assert container,name
        obj=json.loads(run(['docker','inspect',container]))[0]; host=obj['HostConfig']
        assert obj['State']['Running'],name
        assert host['ReadonlyRootfs'] and 'ALL' in host['CapDrop'],name
        assert 'no-new-privileges:true' in host['SecurityOpt'],name
        assert obj['Config']['User']=='10001:10001',name
        if name!='gateway':assert not host['PortBindings'],name
        nets=list(obj['NetworkSettings']['Networks'])
        assert len(nets)==(2 if name.endswith('-relay') else 1),name
        if name in apps:
            assert json.loads(run(['docker','network','inspect',nets[0]]))[0]['Internal'],name
    # The vulnerable API can reach only its own fixed relay by name; forged Host
    # cannot turn that relay into the learning app or another target.
    code="import urllib.request; req=urllib.request.Request('http://api-vulnerable-relay:8080/',headers={'Host':'learn.semester.localhost'}); assert b'Week 10 INSECURE API' in urllib.request.urlopen(req,timeout=3).read()"
    run(COMPOSE+['exec','-T','api-vulnerable','python','-c',code])
    code="import socket\nfor name in ('learning-relay','api-defended','gateway'):\n try: socket.getaddrinfo(name,5000)\n except socket.gaierror: continue\n raise AssertionError('unexpected cross-network DNS: '+name)"
    run(COMPOSE+['exec','-T','api-vulnerable','python','-c',code])
    code="import socket\nfor host,port in [('1.1.1.1',443),('169.254.169.254',80)]:\n try: sock=socket.create_connection((host,port),2)\n except OSError: continue\n sock.close(); raise AssertionError('unexpected egress')"
    run(COMPOSE+['exec','-T','api-vulnerable','python','-c',code])
    result={'scope':'Local loopback TLS and Docker isolation; remote VPN/Linux firewall/load tests not performed',
            'https_checks':len(checks),'services':len(config['services']),'checks':checks,
            'passed':['certificate/hostname validation','19 week pages and linked student resources','API 401/403/200 and field binding','chatbot benign response and escaped output','DevSecOps fail-open/fail-closed and legitimate admin','non-root read-only capability-restricted apps','only gateway published on loopback','private app networks and fixed relay','cross-network DNS denied','API Internet and metadata egress denied']}
    (HERE/'evidence').mkdir(exist_ok=True)
    (HERE/'evidence/smoke.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
if __name__=='__main__':main()
