# Uji coba ponytail-audit (2026-10-20)

Skill: `ponytail-audit` dari DietrichGebert/ponytail @ 09c434a (plugin tidak terpasang di sesi; aturannya diterapkan manual).
Beban yang diasumsikan: satu pemilik, 1–2 bot aktif, satu VM Proxmox 6 GB.

**Apa repo ini:** satu Murmur + satu Hermes (profil per bot) + satu komputer OpenBot per bot, dengan sidecar MCP
yang membatasi domain dan plugin Auto Review yang memutuskan allow/approve/deny per tool.

## Must fix
1. **Verifier LLM menilai tanpa melihat isi** (`plugins/auto-review/__init__.py`, `llm_verdict`) — *diperbaiki*
   - Apa: aturan `files-write` bertanya ke LLM sebelum bot menulis berkas.
   - Masalah: argumen dikirim lewat `redact()`, yang menyembunyikan `contents`. LLM hanya melihat path, lalu bisa
     menjawab "allow 0.9" untuk isi apa pun — sebelumnya itu selalu dilihat manusia.
   - Perbaikan: verifier menerima `text`/`contents` (maks 2000 karakter); kunci kredensial tetap disembunyikan. Ada tes.
   - Jika dibiarkan: berkas berbahaya bisa lolos tanpa dilihat siapa pun.

2. **Uji Rakazo bisa jalan tanpa firewall** (`eval/rakazo/run.sh up`) — *diperbaiki*
   - Apa: `up` hanya mengecek tulisan `SANDBOX_COMPUTER_EGRESS=restricted` di `.env`.
   - Masalah: tanpa `run.sh egress`, aturan iptables tidak ada; komputer bot bisa membuka LAN, termasuk UI Proxmox `:8006`.
   - Perbaikan: `up` menolak jalan bila rantai `DOCKER-USER` tidak memuat aturan `rakazo-c`.
   - Jika dibiarkan: bot uji bisa menjangkau hypervisor Anda.

## Nice to have
3. **Flag `llm: true` diabaikan pada aturan tanpa `id`** (`rule_llm`) — *diperbaiki*
   - Masalah: `decide` memberi nama `rule<i>` untuk aturan tanpa id, `rule_llm` hanya mencari `id`. Verifier diam-diam tidak dipakai.
   - Perbaikan: satu baris, nama cadangan yang sama. Ada tes.

Diperiksa dan **bukan** temuan: pola `*.domain` di sidecar sama dengan pencocokan OpenBot (`egress.ts domainMatches`);
`file:`/`javascript:` saat `OPS_ALLOWED_DOMAINS=*` tetap ditolak OpenBot (`request-validation.ts`);
nilai `REVIEW_LLM_MIN_CONFIDENCE` rusak → fail-closed (deny).

Verdict: setelah 1–3, siap diuji di home lab.
Lean: tidak ada kode mati yang ditemukan; repo ±540 baris kode.
Not checked: perilaku runtime (Docker, Chromium, Hermes, panggilan LLM nyata) — tidak bisa dijalankan di sandbox ini.
Batas yang diterima (komentar `shortcut:`): isi berkas bisa memuat prompt injection ke verifier; aman selama aturan `llm` hanya untuk aksi berisiko rendah.
