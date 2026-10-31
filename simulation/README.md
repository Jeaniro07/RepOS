# Simulasi: bot Rakazo memakai plugin ini dari nol

`run_simulation.py` memerankan bot Rakazo yang baru memasang plugin `antislop-video`, lalu membuat satu video
vertikal 20 detik ("Kenapa kopi saya pahit") mengikuti skill langkah demi langkah. Hasil terakhir ada di
[`output/SIMULATION.md`](output/SIMULATION.md).

## Apa yang nyata, apa yang ditiru

| Bagian | Status |
|---|---|
| Parser plugin Rakazo (`parsePluginDirectory` dari elie222/rakazo, seperti tombol **Preview**) | **Nyata** (`rakazo-preview/`, hanya `zod` dan helper jaringan yang di-stub karena npm tidak tersedia) |
| Clone repo ini dari GitHub, `toolkit/setup.sh`, ffmpeg statis, semua perintah `slopguard`, semua render ffmpeg | **Nyata** |
| Komputer bot: user non-root baru, home kosong, Python 3.11, PATH tanpa ffmpeg/ffprobe/node/apt/pip/uv | Ditiru (mirip image Debian komputer Rakazo) |
| fal.ai | Ditiru oleh `fake_fal.py`: protokol queue + storage yang sama, media dibuat lokal (suara flite, still, klip zoom, timestamp kata yang tepat) |
| Footage pengguna | Ditiru (klip placeholder berlabel "simulasi") |
| Tulisan agent (brief, naskah, rencana generasi) | Diambil dari `scenario/` |
| LLM bot dan helper `slop-critic` | Tidak dijalankan (butuh Rakazo + model); keberadaan semua bahan untuk kritikus dicek |

## Jalankan

```bash
python3 simulation/run_simulation.py --ref main                # setelah PR di-merge
python3 simulation/run_simulation.py --ref <branch> --keep     # menguji branch yang belum di-merge
```

Butuh: Linux, `git`, `curl`, Python 3.11 (`python3.11`), ffmpeg dengan filter `flite` di host (untuk suara fal tiruan),
Node 22+ (untuk parser Rakazo), akses ke github.com. Jalankan sebagai root agar user terisolasi `rakazo-sim` bisa dibuat;
tanpa root, simulasi tetap jalan sebagai user saat ini dengan home dan PATH terisolasi.

## Yang ditemukan dan diperbaiki oleh simulasi

1. Rakazo menolak **seluruh** skill bila foldernya berisi file non-teks (mis. `.py`); `validate_plugin.py` kini menganggapnya error.
2. `setup.sh` menaruh ffmpeg di luar PATH, padahal skill perakitan memanggil `ffmpeg` langsung; kini ditautkan ke `~/.local/bin`.
3. `slopguard fal run` mengembalikan path relatif yang mudah salah diteruskan; kini absolut, dan path lokal yang tidak ada
   gagal **sebelum** panggilan berbayar.
4. Build ffmpeg master (dev) macet 99% CPU saat caption dan audio berada di satu filtergraph; `setup.sh` kini memakai rilis
   stabil 8.1, dan skill perakitan membakar caption dan mux audio di pass terpisah dengan `timeout -s KILL`.
5. Perintah baru agar agent tidak berimprovisasi pada langkah deterministik: `slopguard captions` (timestamp kata → SRT)
   dan `slopguard master` (loudness dua pass).
6. Agent menjalankan perintah tanpa terminal. Dengan stdin tertutup, ffmpeg membaca byte file input sebagai perintah
   keyboard (data rusak, lalu menunggu selamanya sampai dibunuh). Semua pemanggilan ffmpeg kini memakai `-nostdin`
   (slopguard memaksanya; skill perakitan mewajibkannya), dan setiap render dibatasi `timeout -s KILL`.
7. Contact sheet memperlihatkan caption 2 baris (di SRT) tampil 4 baris di layar: 42 karakter/baris terlalu panjang untuk
   lebar vertikal 1080 px, dan angka QA tidak bisa melihatnya. `slopguard captions` kini memakai 28 karakter/baris untuk
   proyek vertikal, pemeriksaan memakai batas 32, dan skill perakitan menyuruh agent mengecek wrapping di contact sheet.
