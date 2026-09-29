"""Initialize local secrets without putting a password in shell history."""
from pathlib import Path
from getpass import getpass
import secrets
import os
root = Path(__file__).resolve().parents[1]
target = root / '.env'
if target.exists():
    raise SystemExit('.env already exists and was not overwritten. Edit it directly.')
password = getpass('Choose a workspace password (12-256 characters): ')
if not 12 <= len(password) <= 256 or '\n' in password or '\r' in password:
    raise SystemExit('Use 12-256 characters without line breaks.')
if getpass('Confirm workspace password: ') != password:
    raise SystemExit('Passwords did not match. Nothing was written.')
quoted = "'" + password.replace('\\', '\\\\').replace("'", "\\'") + "'"
text = (root / '.env.example').read_text()
text = text.replace('APP_PASSWORD=\n', 'APP_PASSWORD=' + quoted + '\n', 1)
text = text.replace('SESSION_SECRET=\n', 'SESSION_SECRET=' + secrets.token_urlsafe(48) + '\n', 1)
target.write_text(text)
try: os.chmod(target, 0o600)
except OSError: pass
print('Created .env. Add optional API keys there; never commit this file.')
print('Start: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000')
