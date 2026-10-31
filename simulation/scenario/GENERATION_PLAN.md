# Rencana generasi fal.ai (menunggu persetujuan)

| # | Endpoint | Untuk | Jumlah | Catatan |
|---|---|---|---|---|
| 1 | fal-ai/elevenlabs/tts/eleven-v3 | narasi (5 kalimat) | 1 | satu suara tetap untuk channel |
| 2 | fal-ai/elevenlabs/speech-to-text/scribe-v2 | timestamp per kata untuk potongan & caption | 1 | |
| 3 | fal-ai/nano-banana-pro | still shot 4: uap di atas cangkir | 1 | tidak ada orang, tidak ada teks |
| 4 | bytedance/seedance-2.0/image-to-video | gerak 4 detik dari still shot 4 | 1 | |

Total 4 panggilan = batas proyek (`fal.max_calls` = 4). Harga per endpoint dicek di halaman model fal sebelum dijalankan.
Shot 1, 2, 5 dari footage pengguna; shot 3 digambar dengan kode. Porsi generatif sekitar 20% durasi.
