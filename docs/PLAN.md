# Rencana RepOS

## Keputusan
- **Fondasi**: Murmur (UI) + Hermes (agen: Buddy, Apps/OAuth, Telegram/WhatsApp, rutinitas, /goal). Tidak membangun ulang.
- **Satu Hermes, satu profil per bot** (`/opt/data/profiles/<bot>/`), bukan satu Hermes per bot: lebih hemat RAM di home-lab; isolasi kuat untuk bot sensitif ditunda ke Fase 2.
- **Komputer per bot** = OpenBot *agent-computer* (Playwright/Chromium, CDP screencast, takeover, request_help, masking rahasia, egress policy), satu container per bot dengan token & volume sendiri. Bukan noVNC.
- **Teach-mode**: demonstrasi di OpenBot → draft → `SKILL.md` Hermes (`teach/draft-to-skill.ts`). Skill tidak memberi izin.
- **Auto Review**: plugin `pre_tool_call` berbasis aturan (deny/allow/approve), mode `dry-run` lalu `enforce`, audit JSONL, fail-closed. Lapis kedua: allowlist domain di sidecar + egress policy Chromium.

## Bot
| Bot | Fase 0 |
|---|---|
| Ops Holding | pilot: profil + komputer + MCP |
| Penyidikan | profil terkunci saja (tanpa komputer, tanpa MCP, policy default-deny) |
| Xaqu, Media, Website & Aplikasi, Trading | belum — tambah `bots/<n>/` + service komputer bila perlu |

## Fase
- **Fase 0 (repo ini)**: fondasi, pilot Ops Holding, dry-run offline.
- **Fase 1 (di home-lab)**: jalankan, lengkapi checklist `docs/VERIFICATION.md` bagian "perlu home-lab", aktifkan `enforce` setelah audit dry-run bersih, ajari 1–2 skill lewat teach.
- **Fase 2**: Hermes terpisah di jaringan `internal: true` + LLM lokal untuk Penyidikan (isolasi nyata); bot lain.

## Tidak ada di Fase 0 (jujur)
- Auto Review: aturan + verifier LLM opsional (hanya aturan `llm: true`, lihat `docs/MERGED.md`); sisanya persetujuan manusia.
- Isolasi Penyidikan masih tingkat konfigurasi; LLM tetap cloud.
- Image Murmur hanya dikunci tag (bukan digest).
