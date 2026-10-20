# Menjalankan di home-lab (Proxmox + Tailscale)

Mesin: Core i3 gen 4 (2 inti/4 thread), RAM 8 GB, Proxmox VE, Tailscale.

## 1. VM di Proxmox (bukan LXC)
Pakai **VM**, bukan LXC: Docker + Chromium di LXC butuh nesting dan sandbox Chromium sering gagal di container tak-istimewa.

| Setelan | Nilai | Alasan |
|---|---|---|
| OS | Debian 12/13 netinst, tanpa desktop | paling hemat RAM |
| CPU | 4 vCPU, type `host` | Chromium butuh instruksi CPU asli |
| RAM | 6144 MB, ballooning **mati** | sisa ±2 GB untuk Proxmox; balloon mencuri RAM saat Chromium aktif |
| Disk | 40 GB, `discard=on`, SSD emulation | image + profil browser |
| Lainnya | QEMU guest agent aktif, start at boot | |

Jika Proxmox memakai ZFS, batasi ARC (default bisa memakan setengah RAM host):
`echo "options zfs zfs_arc_max=1073741824" > /etc/modprobe.d/zfs.conf && update-initramfs -u` lalu reboot host.

Di dalam VM: Docker Engine + Compose plugin, swap 4 GB sebagai pengaman
(`fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`, tambahkan ke `/etc/fstab`).

Anggaran RAM container (batas di `compose.yaml`): Murmur 0,5 + Hermes 1,5 + komputer Ops 2 + sidecar 0,1 ≈ 4,1 GB.
Hanya **satu** komputer bot aktif di mesin ini. Uji Rakazo (`eval/rakazo/`) jalankan bergantian, jangan bersamaan.

## 2. Pasang RepOS
1. `git clone` repo, `git checkout phase0/foundation`.
2. `cp .env.example .env`, isi semua nilai (`openssl rand -hex 24`; `OPS_COMPUTER_TOKEN` ≠ `OPS_MCP_TOKEN`, sidecar menolak start bila sama), `OPS_ALLOWED_DOMAINS` (mis. `example.com,*.bankanda.co.id`), dan API key LLM untuk Hermes. Verifier `REVIEW_LLM_*` opsional.
3. `scripts/fetch-openbot.sh` → `scripts/dc up -d --build` → `scripts/seed.sh`.
4. `scripts/dryrun.sh` harus 10 lolos.

## 3. Akses lewat Tailscale
Tailscale dipasang **di dalam VM** (bukan di host Proxmox), supaya hanya Murmur yang terlihat di tailnet:
```
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale serve --bg 3000      # https://<nama-vm>.<tailnet>.ts.net -> 127.0.0.1:3000
```
Murmur menerima nama `*.ts.net` tanpa setelan tambahan dan menandai cookie `Secure` di HTTPS.
**Jangan** pakai `tailscale funnel` (itu membuka ke internet publik), dan jangan forward port 3000 di router.
Hermes, komputer bot, dan sidecar tidak punya port di host; hanya Murmur di 127.0.0.1:3000.

## 4. Sebelum enforce
Biarkan `mode: dry-run` di `plugins/auto-review/policy.yaml` beberapa hari; baca `profiles/ops-holding/auto-review.jsonl`,
rapikan aturan, lalu ubah ke `mode: enforce` (dibaca ulang otomatis; `AUTOREVIEW_MODE` menimpa).
Lalu jalankan checklist "perlu home-lab" di `VERIFICATION.md` dan catat hasilnya, termasuk `docker stats`.
