#!/usr/bin/env python3
"""Merge bots/<nama>/{config.yaml,SOUL.md} ke <HERMES_HOME>/profiles/<nama>/. Idempoten; nilai dict digabung, lainnya ditimpa.

Pakai: seed.py <bots_dir> [<hermes_home>]   (hermes_home default: $HERMES_HOME atau /opt/data)
"""
import os
import shutil
import sys
from pathlib import Path

import yaml


def merge(base, new):
    for k, v in new.items():
        base[k] = merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return base


def seed(bots_dir, home):
    done = []
    for bot in sorted(p for p in Path(bots_dir).iterdir() if (p / "config.yaml").exists()):
        dest = Path(home) / "profiles" / bot.name
        dest.mkdir(parents=True, exist_ok=True)
        cfg_path = dest / "config.yaml"
        cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
        cfg_path.write_text(yaml.safe_dump(merge(cfg or {}, yaml.safe_load((bot / "config.yaml").read_text())), sort_keys=False, allow_unicode=True))
        if (bot / "SOUL.md").exists():
            shutil.copyfile(bot / "SOUL.md", dest / "SOUL.md")
        done.append(bot.name)
    return done


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    home = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("HERMES_HOME", "/opt/data")
    print("profil di-seed:", ", ".join(seed(sys.argv[1], home)) or "(tidak ada)")
