# Gabungan terbaik: RepOS + Rakazo + OpenBot + Hermes

Target hardware: Core i3 gen 4, 8 GB RAM (VM Proxmox 6 GB) → **satu stack ringan**, bukan dua. Rakazo tidak dijalankan
permanen; hanya diambil ide-idenya. Sumber: kode Rakazo commit 08ee8cf, OpenBot e8bb273.

| Kemampuan | Dipakai dari | Status di repo |
|---|---|---|
| Chat, Buddy, WhatsApp/Telegram, rutinitas, /goal | Hermes + Murmur (Xaqu sudah ada) | Fase 0 |
| Komputer per bot, layar CDP (bukan noVNC) | OpenBot agent-computer | Fase 0 |
| Allowlist domain per bot | RepOS sidecar (Rakazo hanya blok jaringan privat → RepOS lebih ketat) | Fase 0 |
| Aturan deny/approve per bot, audit JSONL | RepOS plugin Auto Review | Fase 0 |
| **Verifier LLM + batas keyakinan + fail ke manusia** | **Rakazo Auto Review** | **Baru: `llm_verdict`** |
| Token sidecar ≠ token komputer, tanpa /exec | RepOS | Fase 0 |
| Teach-mode → skill | RepOS `teach/` (Rakazo punya UI rekam; belum ditiru) | Fase 0 (CLI) |
| Batas sumber daya | RepOS compose | **Baru: `mem_limit` total ≈ 4,2 GB** |
| Multi-bot Telegram per bot | Hermes profile (setara `TELEGRAM_BOT_TOKEN_<NAMA>` Rakazo) | Fase 1 |
| Firewall host untuk komputer | tidak perlu: OpenBot `/egress-policy` allowlist sudah lebih ketat | — |

## Aturan LLM verifier (aman by design)
- Hanya aturan `approve` yang bertanda `llm: true` yang bertanya ke LLM (saat ini `files-write` Ops Holding).
- Aturan `deny`, dan `approve` tanpa `llm` (mis. teks pembayaran), tidak pernah bisa diloloskan LLM.
- `allow`/`deny` hanya dipakai bila keyakinan ≥ `REVIEW_LLM_MIN_CONFIDENCE` (default 0,8); selain itu, timeout
  (`REVIEW_LLM_TIMEOUT`, 8 dtk), error, atau keluaran rusak → persetujuan manusia.
- Argumen diredaksi sebelum dikirim. Penyidikan tidak memakai verifier (tanpa internet).
- Risiko tersisa: `REVIEW_LLM_KEY` ada di environment container Hermes bersama (sama seperti `OPS_MCP_TOKEN`);
  aman selama profil dengan terminal tidak ada. Pakai kunci berbatas anggaran.

## Anggaran RAM (perkiraan batas, belum diukur)
Murmur 0,5 + Hermes 1,5 + komputer Ops 2 + sidecar 0,1 = ~4,1 GB, sisa ~3,5 GB untuk OS/swap. Satu komputer bot aktif.
Tambahkan swap 4 GB sebagai pengaman. Ukur dengan `docker stats` di home lab.

## Belum diverifikasi
Panggilan LLM nyata (diuji dengan fake), kecukupan batas memori di mesin Anda, dan hook `approve` di Hermes saat verifier
mengembalikan `allow`. Lihat `docs/VERIFICATION.md`.
