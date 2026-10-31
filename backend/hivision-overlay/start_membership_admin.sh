#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ -f .env.miniapp ]; then . ./.env.miniapp; fi
if [ -f .env.miniapp.payment ]; then . ./.env.miniapp.payment; fi
if [ -f .env.miniapp.admin ]; then . ./.env.miniapp.admin; fi
exec .venv/bin/python miniapp_admin.py
