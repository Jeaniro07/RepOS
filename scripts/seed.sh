#!/bin/sh
# Salin bots/ + seed.py ke kontainer Hermes lalu jalankan. Idempoten. Dijalankan SETELAH `scripts/dc up -d`.
set -eu
cd "$(dirname "$0")/.."
# Hapus dulu: `docker cp bots hermes:/tmp/bots` pada run kedua menyalin ke /tmp/bots/bots (config lama terpakai).
scripts/dc exec -T hermes rm -rf /tmp/bots /tmp/seed.py
scripts/dc cp bots hermes:/tmp/bots
scripts/dc cp hermes/seed.py hermes:/tmp/seed.py
# Jalan sebagai user hermes agar config profil tidak menjadi milik root (Hermes harus bisa menulisnya).
scripts/dc exec -T -u hermes hermes python3 /tmp/seed.py /tmp/bots /opt/data
scripts/dc restart hermes   # gateway memuat plugin & config sekali saat start
