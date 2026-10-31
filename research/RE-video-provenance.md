# Reverse-engineering findings: provenance in AI-generated video files

Dikerjakan dengan skill reverse-engineering pada 2026-10-31. Setiap klaim memakai koordinat (offset byte) dan cara
mengetahuinya: *bytes* (dibaca langsung dari file), *decoder* (CBOR/JUMBF yang saya tulis, dicocokkan dengan
manifest resmi), atau *inferred* (kesimpulan).

## 1. Target identification

| Sampel | Asal | Ukuran | sha256 |
|---|---|---|---|
| `truepic-20230212-zoetrope.mp4` | [c2pa-org/public-testfiles](https://github.com/c2pa-org/public-testfiles) `legacy/1.4/video/mp4/` (CC BY-SA 4.0, tidak disalin ke repo ini) | 15,456,823 | `23db1d78…48cfff3` |
| `dark-theme-demo.mp4` | [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) `assets/readme/` | — | `8572376a…b8b2d3` |
| `style-2a-demo.mp4` | idem | — | `6794a7c0…f8e9` |
| `adobe-20240110-single_manifest_store.pdf` | c2pa-org/public-testfiles `legacy/1.4/pdf/` | 626,615 | (hanya untuk struktur `c2pa.actions` dari Firefly) |
| 15 MP4 lain dari repo stickman dan HyperFrames + render ffmpeg kita | pembanding | — | — |

Jenis: ISO Base Media File Format (`ftyp` pada offset 4). Catatan: `triage.py` dari skill tidak mengenali magic MP4
karena tanda `ftyp` ada di offset 4, bukan 0 (*bytes*).

## 2. Scope and authorization

Interoperabilitas dan penelitian: membaca metadata asal-usul (C2PA Content Credentials) di file video yang kita
proses sendiri, agar agent bisa mengungkapkan konten AI dengan jujur. Tidak ada yang dieksekusi; file media hanya
dibaca sebagai data (`python -I`, folder sampel terpisah).

## 3. Environment and tools

Container cloud Ubuntu 24.04; `triage.py` (skill), walker box/JUMBF dan decoder CBOR yang saya tulis
(sekarang `toolkit/slopguard/provenance.py`), ffmpeg 6.1 untuk uji remux/re-encode.

## 4. Static findings

| Koordinat | Isi | Bukti | Diketahui lewat | Belum diverifikasi |
|---|---|---|---|---|
| zoetrope `0x00` | `ftyp` 24 B, major `mp42`, compat `isom mp42` | dump box | bytes | — |
| zoetrope `0x18` | `uuid` 30,192 B, UUID `d8fec3d6-1b0e-483c-9297-5828877ec481` | dump box | bytes | — |
| zoetrope `0x18+24` | version/flags `00000000`, purpose `"manifest\0"`, merkle offset 8 B = 0, lalu JUMBF | hex `000000006d616e6966657374…` | bytes | arti field merkle (selalu 0 di sampel) |
| JUMBF `+0x000` | superbox `jumb`, `jumd` type `c2pa`+`00110010800000aa00389b71`, label `c2pa` | dump JUMBF | bytes | — |
| JUMBF `+0x026` | manifest `c2ma` label `com.truepic:urn:uuid:74b6ec09-…` | dump | bytes | — |
| JUMBF `+0x081` | `c2as` assertion store: `com.truepic.libc2pa` (cbor), `stds.exif` ×4 (json), `com.truepic.custom.odometry` (cbor), `c2pa.hash.bmff.v2` (cbor) | dump | bytes | isi hash BMFF tidak divalidasi ulang |
| JUMBF `+0xb67` | `c2cl` claim (cbor 1,525 B): `claim_generator "Truepic_Lens_SDK_libc2pa/2.5.1"`, 7 assertion ber-hash sha256 | decode CBOR | decoder, **cocok dengan `manifest_store.json` resmi** | — |
| JUMBF `+0x1188` | `c2cs` signature (cbor 25,608 B) diawali `d2 84 43 a1 01 26` = COSE_Sign1 (tag 18), alg −7 (ES256) | hex | bytes + decoder | **tanda tangan tidak diverifikasi** |
| zoetrope sertifikat | OID rsaEncryption di file `0x5c2f`, `0x61eb`, `0x6766`; OCSP `va.truepic.com` | triage.py | bytes | rantai sertifikat tidak divalidasi |
| dark-theme-demo `0x20` | `uuid` C2PA 6,138 B; manifest `urn:c2pa:06cbb97a-…`; urutan anak: `c2cs`, `c2cl` (`c2pa.claim.v2`), `c2as` | dump | bytes | — |
| dark-theme-demo claim | `claim_generator_info: {name: "Google C2PA Core Generator Library"}` (dict, bukan list), field `created_assertions` (C2PA 2.x) | decode | decoder | — |
| dark-theme-demo `c2pa.actions.v2` | `c2pa.created` "Created by Google Generative AI." + `c2pa.edited` "Applied imperceptible SynthID watermark.", keduanya `digitalSourceType …/trainedAlgorithmicMedia` | decode | decoder | apakah semua alat Google menulis teks yang sama |
| style-2a-demo actions | + `c2pa.opened`, `c2pa.resized` dengan `compositeWithTrainedAlgorithmicMedia` | decode | decoder | — |
| 9 demo stickman | `udta/meta/ilst/©too = "Google"` + kotak C2PA di `0x20` | walker | bytes | — |
| 4 demo + hasil akhir stickman, fixture HyperFrames | `©too = "Lavf62.12.100"`, tanpa C2PA | walker | bytes | — |
| 2 demo stickman | handler `"Twitter-vork muxer"`, tanpa tag, tanpa C2PA | walker | bytes | — |
| 1 demo stickman | handler `"Core Media Video"` + `©too Lavf` | walker | bytes | — |
| PDF Firefly, Flate stream di offset 4557 (`0x11cd`) | manifest bahan: `c2pa.actions` `c2pa.created`, `softwareAgent "Adobe Firefly Pipeline"`, `firefly.operation "text_to_image"`, `trainedAlgorithmicMedia` | inflate stream lalu decode | decoder | — |
| PDF Firefly, store mentah di offset 587472 (`0x8f6d0`) | manifest store yang dibaca `slopguard provenance` (3 action AI, generator Adobe Express/Firefly) | `slopguard provenance` | decoder | — |
| `moov/meta` di MP4 | gaya QuickTime: **tanpa** version/flags (anak pertama langsung `hdlr`), berbeda dari `meta` FullBox ISO | walker salah baca pada versi pertama (size = ASCII "hdlr") | bytes | — |

## 5. Dynamic findings (perlakuan ffmpeg)

| Perlakuan | Hasil | Reproduksi | Belum diverifikasi |
|---|---|---|---|
| `ffmpeg -i dark-theme-demo.mp4 -c copy out.mp4` | kotak C2PA **hilang**; `©too` jadi `Lavf60.16.100` | `toolkit/tests` `test_ffmpeg_remux_drops_credentials` | — |
| `-c copy -movflags +use_metadata_tags` | C2PA hilang, `©too` hilang | perintah di samping | — |
| re-encode libx264/aac | C2PA hilang, `©too Lavf60.16.100` | perintah di samping | apakah watermark SynthID di piksel bertahan (tidak bisa diukur di sini) |

## 6. Format yang dipulihkan

```
ISO BMFF top-level:  ftyp | uuid(C2PA) | moov | free | mdat     (urutan berbeda per penulis)
uuid(C2PA) = size:u32 'uuid' d8fec3d6-1b0e-483c-9297-5828877ec481
             version/flags:u32=0  purpose:"manifest\0"  merkle_offset:u64  JUMBF...
JUMBF superbox = size:u32 'jumb' [ jumd | content-or-superboxes... ]
jumd           = size:u32 'jumd' type:16 (kind[4] + 00110010800000aa00389b71) toggles:u8 [label "\0" if toggles&2]
kinds          = c2pa (store) > c2ma (manifest; active = terakhir) > c2as (assertions) / c2cl (claim) / c2cs (signature)
content        = 'cbor' (claim, actions, hash) | 'json' (stds.exif)
AI declaration = c2pa.actions[.v2].actions[].digitalSourceType = http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia
                 (atau compositeWithTrainedAlgorithmicMedia untuk campuran)
```

## 7. Behavior summary dan dampaknya ke workflow

- Generator AI (Google, Adobe Firefly) menulis klaim AI yang mudah dibaca mesin di file keluarannya.
- **ffmpeg (remux maupun re-encode) membuang klaim itu.** Video akhir yang memuat klip AI tidak lagi membawa
  pernyataan AI, sehingga label otomatis platform yang berbasis C2PA tidak akan terpicu dari file itu. Pengungkapan
  harus dilakukan manual.
- Diimplementasikan di `slopguard`:
  - `slopguard provenance <file|folder>`: membaca kotak C2PA, klaim, action, generator, dan tag encoder
    (tanda tangan tidak diverifikasi);
  - `check-ledger`: **FLOOR `ledger.provenance-mismatch`** bila file yang dicatat sebagai footage/capture/arsip/stok
    ternyata menyatakan dirinya buatan AI;
  - `qa`: **REFLEX `provenance.lost`** bila file di `assets/` atau `gen/` menyatakan AI tetapi render akhir tidak
    membawa kredensial apa pun.

## 8. Open questions / next steps

- Verifikasi tanda tangan COSE dan rantai sertifikat (butuh library kriptografi; `contentauth/c2pa-python` bisa dipakai
  bila tersedia).
- Sampel dari generator lain (OpenAI Sora, Runway, Kling, Seedance, Hailuo) belum tersedia di sesi ini, jadi pola
  `©too`/`claim_generator` mereka belum terkonfirmasi. Parser membaca struktur standar, jadi seharusnya tetap bekerja.
- Kotak XMP (`uuid` lain) dan C2PA di JPEG/PNG hanya ditangani lewat pemindaian JUMBF umum (terbukti pada PDF).
- Menulis ulang manifest C2PA ke render akhir (sebagai ingredient) butuh penandatangan; di luar cakupan.
