#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  .venv/bin/python -c "from pathlib import Path; import secrets; p=Path('.env'); p.write_text(p.read_text().replace('replace-with-a-long-random-secret',secrets.token_urlsafe(48)))"
fi
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
printf '\nReady: .venv/bin/python manage.py runserver\n'
