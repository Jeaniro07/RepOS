# Contoh proyek: "Kenapa kopi saya pahit"

Artefak yang dihasilkan bot untuk video vertikal 16 detik. Videonya sendiri tidak disertakan (footage milik pengguna).

| File | Isi |
|---|---|
| `script.md` | Naskah bersih: satu klaim per kalimat, angka diberi `[1]`, sumber tercantum |
| `script-slop.md` | Versi slop untuk perbandingan |
| `ledger.csv` | 5 shot: 4 footage sendiri + 1 diagram dari kode; tidak ada generatif |
| `master.srt` | Caption di timeline output, <= 42 karakter per baris |
| `slopguard.json` | Format, durasi, bahasa, loudness, batas 4 panggilan fal.ai |

Coba:

```bash
slopguard lint-script examples/kopi-pahit/script.md        # CLEAR (exit 0)
slopguard lint-script examples/kopi-pahit/script-slop.md   # BLOCKED (exit 1): 2 klaim tanpa sumber + 12 REFLEX
slopguard check-ledger examples/kopi-pahit/ledger.csv      # CLEAR
slopguard check-captions examples/kopi-pahit/master.srt    # CLEAR
```
