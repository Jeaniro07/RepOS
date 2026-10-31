# antislop-video: plugin Rakazo

Plugin skills + MCP untuk bot Rakazo yang membuat video tanpa "AI slop".

## Isi

| Bagian | File | Fungsi |
|---|---|---|
| Skill utama | `skills/antislop-video-director/` | Alur kerja brief → cerita → SPEC → naskah → ledger → aset → rakit → QA → serah; aturan Floor; bahan tidak boleh dipalsukan |
| Skill | `skills/antislop-script/` | Menulis narasi yang terdengar seperti manusia, semua fakta bersumber |
| Skill | `skills/fal-media/` | Pakai fal.ai (gambar, video, suara, transkrip) dengan rencana yang disetujui dan batas anggaran |
| Skill | `skills/video-assembly/` | Merakit dengan ffmpeg / HyperFrames / Remotion / Manim + aturan produksi wajib |
| Skill | `skills/video-qa/` | QA terukur, contact sheet, kritikus independen, `REVIEW.md` |
| Skill | `skills/video-toolkit-setup/` | Pasang `slopguard` + ffmpeg statis di komputer bot, simpan kunci fal.ai dengan aman |
| Perintah | `commands/video.md` | `/video <topik/link/naskah>` |
| Perintah | `commands/cek-slop.md` | `/cek-slop <file>` |
| Helper | `agents/slop-critic.md` | Subagent kritikus dengan konteks bersih |
| MCP | `mcp.json` | Server MCP resmi fal.ai `https://mcp.fal.ai/mcp` |

## Pasang

1. Rakazo → **Integrations** → **+** → **From GitHub**.
2. Tempel `https://github.com/Jeaniro07/RepOS/tree/main/rakazo-plugin` → **Preview**.
3. **Connect** server `fal` dan **Add skills**.
4. **Manage MCP servers** → `fal` → **Advanced** → **Access token** = kunci fal.ai Anda → simpan →
   **Use in this bot**. (Opsional; skill juga bisa memakai kunci sebagai command variable `$FAL_KEY`.)

Rakazo hanya membaca file teks plugin; skrip tidak dijalankan dari sini. Alat ukur (`slopguard`) dipasang bot
di komputernya sendiri lewat skill `video-toolkit-setup` (clone repo ini + `toolkit/setup.sh`).

Validasi lokal sebelum dipublikasikan: `python3 scripts/validate_plugin.py rakazo-plugin`.
