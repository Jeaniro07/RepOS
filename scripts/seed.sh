#!/bin/sh
# Salin bots/ + seed.py ke kontainer Hermes lalu jalankan. Idempoten. Dijalankan SETELAH `scripts/dc up -d`.
set -eu
cd "$(dirname "$0")/.."
scripts/dc cp bots hermes:/tmp/bots
scripts/dc cp hermes/seed.py hermes:/tmp/seed.py
scripts/dc exec -T hermes python3 /tmp/seed.py /tmp/bots /opt/data
scripts/dc restart hermes   # gateway memuat plugin & config sekali saat start
