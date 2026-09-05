"""Create a local secret without overwriting an existing deployment."""
import os
from pathlib import Path
import secrets
path=Path(__file__).with_name('.env')
try:
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
except FileExistsError:
    print('Existing .env retained.')
else:
    with os.fdopen(fd,'w') as f:
        f.write('SEMESTER_SECRET_KEY='+secrets.token_urlsafe(48)+'\n')
        f.write('SEMESTER_BIND_ADDRESS=127.0.0.1\nSEMESTER_HTTPS_PORT=9443\n')
    print('Created private local configuration; teacher registration stays closed.')
