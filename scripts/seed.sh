#!/bin/sh
# Salin bots/ + seed.py ke kontainer Hermes lalu jalankan. Idempoten. Dijalankan SETELAH `scripts/dc up -d`.
set -eu
cd "$(dirname "$0")/.."
# Hapus dulu: `docker cp bots hermes:/tmp/bots` pada run kedua menyalin ke /tmp/bots/bots (config lama terpakai).
scripts/dc exec -T hermes rm -rf /tmp/bots /tmp/seed.py
scripts/dc cp bots hermes:/tmp/bots
scripts/dc cp hermes/seed.py hermes:/tmp/seed.py
# Jalan sebagai user hermes agar config profil tidak menjadi milik root (Hermes harus bisa menulisnya).
# Python milik Hermes (shebang perintah `hermes`), karena python3 sistem di image belum tentu punya parser YAML.
PY=$(scripts/dc exec -T hermes sh -c 'head -1 "$(command -v hermes)" | sed "s/^#!//"' || true)
case "$PY" in /*python*) ;; *) PY=python3 ;; esac   # $PY sengaja tanpa kutip di bawah: bisa "/usr/bin/env python3"
scripts/dc exec -T -u hermes hermes $PY /tmp/seed.py /tmp/bots /opt/data
scripts/dc restart hermes   # gateway memuat plugin & config sekali saat start
# Plugin yang gagal di-import dilewati Hermes tanpa memblok apa pun: buktikan bisa dimuat, atau gagal keras.
scripts/dc exec -T hermes $PY -c 'import importlib.util as u; s = u.spec_from_file_location("ar", "/opt/data/profiles/ops-holding/plugins/auto-review/__init__.py"); s.loader.exec_module(u.module_from_spec(s)); print("auto-review: bisa dimuat")'
