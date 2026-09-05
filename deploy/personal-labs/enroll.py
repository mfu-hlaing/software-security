"""Private operator CLI: enroll exact IDs; never prints passwords or imports a roster into Git."""
import argparse
import json
from pathlib import Path
import secrets
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'labs/live-quiz'))
import learner_store

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('roster',type=Path)
parser.add_argument('delivery_directory',type=Path)
args=parser.parse_args()
args.delivery_directory.mkdir(mode=0o700,parents=True,exist_ok=True)
for row in json.loads(args.roster.read_text()):
    password=secrets.token_urlsafe(18)
    learner_store.enroll(row['student_id'],row['name'],row['slot'],row['vpn_ip'],password)
    path=args.delivery_directory/(row['student_id']+'.json')
    with path.open('x') as output:
        path.chmod(0o600)
        json.dump({'student_id':row['student_id'],'name':row['name'],'password':password,
                   'vpn_ip':row['vpn_ip'],'login_url':row['login_url']},output,indent=2)
print('Private learner accounts created; deliver each protected credential file only to its owner.')
