"""Refresh public student-document metadata; never crawl instructor/admin routes."""
import concurrent.futures
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://learn.zcr.ai/learn/software-security/'

def fetch(item):
    url = BASE + item['slug'] + '/' + item['kind']
    row = dict(item, url=url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CourseSourceAudit/1.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            if not response.url.startswith(BASE):
                raise ValueError('Redirect outside public course scope')
            body = response.read(2_000_000)
            row.update(status=response.status, sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
            title = re.search(rb'<title>(.*?)</title>', body, re.S)
            row['title'] = title[1].decode('utf-8', 'replace') if title else ''
    except Exception as exc:
        row.update(status='unavailable', error=str(exc)[:180])
    return row

if __name__ == '__main__':
    jobs=[]
    for unit in sorted((ROOT/'labs').glob('week[0-9][0-9]-*')):
        for kind, filename in [('readme','README.md'), ('worksheet','worksheet.md'), ('slides',None), ('mock-ctf','mock-ctf.md'), ('ctf','ctf.md'), ('exam','exam.md'), ('scrimmage','scrimmage.md')]:
            if filename is None or (unit/filename).exists():
                jobs.append({'week':int(unit.name[4:6]),'slug':unit.name,'kind':kind})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(fetch,jobs))
    out={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Public course lectures and student guides only; metadata crawl, no answer keys or student records.','documents':rows}
    (ROOT/'docs/semester-journey/public-crawl.json').write_text(json.dumps(out,indent=2)+'\n')
    print(f'{len(rows)} public documents checked; {sum(x["status"]==200 for x in rows)} available')
