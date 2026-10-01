"""Local setup. Secrets never appear in stdout or chat."""
import secrets,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'.env'
if p.exists():raise SystemExit('.env exists; edit locally instead of overwriting')
s=(p.parent/'.env.example').read_text()
s=s.replace('WATCHKEEPER_API_TOKEN=\n','WATCHKEEPER_API_TOKEN='+secrets.token_urlsafe(48)+'\n').replace('WATCHKEEPER_WEBHOOK_SECRET=\n','WATCHKEEPER_WEBHOOK_SECRET='+secrets.token_urlsafe(48)+'\n')
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(s)
print('Created .env. Enter your Plex URL and owner token there locally, then start Docker Compose. Dry-run mode is on.')
