# SPEC: Kenapa kopi saya pahit

GOAL:    penonton menurunkan suhu air ke ~92 derajat di seduhan berikutnya
OUTPUT:  1080x1920 @ 30 fps, ~20s, -14 LUFS, true peak <= -1 dBTP
HOOK:    frame 0 = kopi dituang (footage pengguna); baris 1 "Kopi saya selalu pahit, padahal bijinya mahal."
LOOK:    latar footage asli; diagram: latar #1d1a17, tinta #f4efe6, aksen #e0703a hanya pada angka suhu;
         DejaVu Sans Bold 96 px angka, 44 px label
TYPE:    caption 58 px, MarginV 380 px (di atas tombol platform), maks 2 baris, <= 17 karakter/detik
MOTION:  diagram: batang suhu turun 100 -> 92 dalam 30 frame ease-out; satu gerakan utama per shot
SOUND:   narasi saja; tidak ada musik; tidak ada SFX
SHOTS:   1 tuang (footage) | 2 ketel (footage) | 3 diagram suhu (kode) | 4 uap di cangkir (generatif, fal) | 5 cicip (footage)
BANNED:  void gelap dengan elemen melayang; glow; semua fade+slide up; Ken Burns sebagai pengganti cerita;
         kartu judul diam; potongan metronom; emoji; ajakan like/subscribe
QA:      frame 0 menampilkan kopi; shot 3 angka terbaca di 360 px; caption tidak menutupi cangkir
