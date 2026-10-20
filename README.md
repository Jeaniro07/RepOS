# RepOS

Bot self-hosted yang selalu hidup: **satu Hermes (profil per bot) + satu komputer (container) per bot**, UI lewat Murmur.
Fase 0 = fondasi + pilot **Ops Holding**. Penyidikan hanya disiapkan sebagai profil terkunci (tanpa browser/internet/konektor).

```
Murmur ──► Hermes (profil: ops-holding, penyidikan, …)
              │  plugin auto-review (pre_tool_call: deny / allow / approve, audit JSONL)
              ▼
         ops-mcp (sidecar MCP, 1 file Bun) ──► ops-computer (OpenBot agent-computer: Chromium + CDP screencast, egress allowlist)
```

| Bagian | Berkas | Bahasa |
|---|---|---|
| Orkestrasi | `compose.yaml`, `versions.env`, `scripts/dc` | YAML |
| Profil bot | `bots/<bot>/config.yaml`, `SOUL.md`, `hermes/seed.py` | YAML + Python (stdlib+PyYAML) |
| Auto Review | `plugins/auto-review/` (`policy.yaml` = aturan) | Python |
| Komputer per bot | `computer-mcp/server.ts` (tanpa dependensi) | Bun/TS |
| Teach-mode | `teach/draft-to-skill.ts` | Bun/TS |

## Pakai
```
cp .env.example .env            # isi kata sandi/token (openssl rand -hex 24)
scripts/fetch-openbot.sh        # ambil OpenBot pada commit terkunci → vendor/openbot
scripts/dc up -d --build
scripts/seed.sh                 # pasang profil bot ke Hermes
```
Langkah lengkap + cek di home-lab: [`docs/HOMELAB.md`](docs/HOMELAB.md).

## Dry-run (offline, tanpa Docker daemon)
```
scripts/dryrun.sh
```
Apa yang sudah dan belum terbukti: [`docs/VERIFICATION.md`](docs/VERIFICATION.md). Rencana & fase: [`docs/PLAN.md`](docs/PLAN.md).
