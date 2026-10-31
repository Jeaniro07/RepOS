# Routine opsional

Minta di chat bot (bot akan membuat routine-nya), atau buat di **Agent computer → Routines**.
Semua routine di bawah hanya membaca/mengukur dan melapor; tidak ada yang mengunggah atau membelanjakan.

## 1. QA otomatis saat ada render baru

> "Pantau folder `~/videos` setiap 15 menit. Kalau ada `edit/final.mp4` atau `edit/preview.mp4` yang baru atau berubah,
> jalankan `slopguard qa` di proyek itu, lalu kirim ringkasan verdict, angka loudness/true peak, temuan FLOOR,
> dan 5 REFLEX teratas ke chat ini. Jangan memperbaiki apa pun tanpa saya minta."

Trigger: **When something changes** → files or folders → `~/videos`.

## 2. Cek naskah mingguan

> "Setiap Senin jam 08.30, jalankan `slopguard lint-script` untuk semua `script.md` yang berubah minggu lalu di `~/videos`,
> laporkan klaim tanpa sumber dan skor slop per proyek."

Trigger: **On a schedule** → weekly.

## 3. Update toolkit bulanan

> "Setiap tanggal 1, `git -C ~/antislop/RepOS pull --ff-only`, jalankan `bash ~/antislop/RepOS/toolkit/setup.sh`
> dan laporkan hasil `slopguard doctor`."

Trigger: **On a schedule** → monthly.

Catatan: routine yang memantau output perintah (command watch) selalu meminta persetujuan di Rakazo; itu disengaja.
