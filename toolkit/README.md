# slopguard

Gate kualitas anti-slop untuk produksi video berbantuan AI. Python standar saja (3.10+), butuh ffmpeg
(ffprobe opsional). Dibuat untuk berjalan di komputer bot Rakazo, tetapi jalan di Linux/macOS mana pun.

```bash
bash toolkit/setup.sh          # pasang ffmpeg statis bila perlu + perintah `slopguard`
slopguard doctor
```

| Perintah | Fungsi |
|---|---|
| `slopguard init <dir> --title T --format vertical --duration 45 --lang id` | Buat folder proyek: `BRIEF.md`, `SPEC.md`, `script.md`, `ledger.csv`, `waivers.json`, `project.md`, `slopguard.json` |
| `slopguard lint-script script.md` | Frasa stok (ID + EN), klaim tanpa sumber, hook generik, ajakan pancingan, ritme monoton, kepanjangan |
| `slopguard check-captions file.srt [--video v.mp4]` | Tumpang tindih, melewati akhir video, kecepatan baca, panjang baris, cue kilat, emoji |
| `slopguard check-ledger ledger.csv` | Sumber & lisensi setiap shot, orang nyata sintetis, porsi generatif, visual berulang |
| `slopguard qa video.mp4 [--captions s.srt]` | Ukuran/aspek, fps, loudness & true peak, jeda mati, frame hitam/beku, cut metronom, frame pertama; + contact sheet |
| `slopguard sheet video.mp4 --cuts` | Contact sheet dan strip sebelum/sesudah potongan |
| `slopguard fal run <endpoint> --input in.json --confirm` | Generasi fal.ai dengan batas jumlah panggilan per proyek dan log |

Kode keluar: 0 bersih, 1 gagal FLOOR, 2 REFLEX masih terbuka, 3 kesalahan pemakaian/setup.

Tingkat gate: **FLOOR** tidak pernah lolos (tidak bisa di-waive), **REFLEX** default yang terasa dibuat mesin
(perbaiki atau waive di `waivers.json` dengan alasan), **FINISH** catatan kerajinan. Tabel lengkap:
`rakazo-plugin/skills/antislop-video-director/references/floor.md`.

Tes: `python3 -m unittest discover -s tests` (membuat video sintetis dengan ffmpeg; server fal tiruan).

Batas jujur: alat ini mengukur. Ia tidak menonton atau mendengar. Lolos semua gate bukan berarti videonya bagus;
itu tugas review dengan mata segar (`slop-critic`).
