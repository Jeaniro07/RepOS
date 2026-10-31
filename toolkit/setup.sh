#!/usr/bin/env bash
# slopguard setup for a Rakazo bot computer (or any Linux/macOS box).
#
# The Rakazo computer runs as uid 1000 with no package manager access, has
# python3, git, curl and uv, but no ffmpeg. This script:
#   1. finds ffmpeg/ffprobe, or downloads a static build (BtbN/FFmpeg-Builds,
#      GPL, linux64 / linuxarm64) into ~/.local/share/slopguard/bin;
#   2. falls back to the imageio-ffmpeg wheel (ffmpeg only) through uv;
#   3. installs a `slopguard` command into ~/.local/bin (and links ffmpeg/ffprobe
#      there when they are not already on PATH);
#   4. runs `slopguard doctor`.
# Safe to re-run. Never touches FAL_KEY or any other secret.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SG_HOME="${HOME}/.local/share/slopguard"
BIN="${SG_HOME}/bin"
mkdir -p "${BIN}" "${HOME}/.local/bin"

have() { command -v "$1" >/dev/null 2>&1; }

ffmpeg_ok() {
  { have ffmpeg && have ffprobe; } || { [ -x "${BIN}/ffmpeg" ] && [ -x "${BIN}/ffprobe" ]; }
}

install_static() {
  local os arch plat url tmp asset ok rel
  os="$(uname -s)"; arch="$(uname -m)"
  if [ "${os}" != "Linux" ]; then
    echo "static download is Linux-only; on macOS run: brew install ffmpeg" >&2
    return 1
  fi
  case "${arch}" in
    x86_64|amd64) plat="linux64" ;;
    aarch64|arm64) plat="linuxarm64" ;;
    *) echo "unsupported arch ${arch}" >&2; return 1 ;;
  esac
  # Prefer a stable release branch. The master (dev) snapshot has been seen to hang
  # when captions and audio share one filtergraph; it is only the last resort.
  # Override with SLOPGUARD_FFMPEG_RELEASE=8.2 (for example) when a newer branch ships.
  rel="${SLOPGUARD_FFMPEG_RELEASE:-8.1}"
  tmp="$(mktemp -d)"
  ok=0
  local retry="--retry 4 --retry-delay 3"
  curl --help all 2>/dev/null | grep -q -- "--retry-all-errors" && retry="${retry} --retry-all-errors"
  for asset in "ffmpeg-n${rel}-latest-${plat}-gpl-${rel}.tar.xz" "ffmpeg-master-latest-${plat}-gpl.tar.xz"; do
    url="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/${asset}"
    echo "downloading ${url} (about 150 MB)..."
    # shellcheck disable=SC2086
    if curl -fsSL ${retry} -o "${tmp}/ff.tar.xz" "${url}"; then ok=1; break; fi
    echo "download failed: ${asset}" >&2
  done
  [ "${ok}" = 1 ] || { rm -rf "${tmp}"; return 1; }
  # Extract only the two binaries with Python (no xz-utils needed).
  python3 - "${tmp}/ff.tar.xz" "${BIN}" <<'PY'
import os, sys, tarfile
src, dest = sys.argv[1], sys.argv[2]
with tarfile.open(src, "r:xz") as tf:
    for m in tf.getmembers():
        name = os.path.basename(m.name)
        if m.isfile() and name in ("ffmpeg", "ffprobe") and "/bin/" in m.name:
            f = tf.extractfile(m)
            out = os.path.join(dest, name)
            with open(out + ".tmp", "wb") as fh:
                fh.write(f.read())
            os.chmod(out + ".tmp", 0o755)
            os.replace(out + ".tmp", out)
            print("installed", out)
PY
  rm -rf "${tmp}"
  [ -x "${BIN}/ffmpeg" ]
}

install_imageio() {
  have uv || return 1
  echo "falling back to imageio-ffmpeg (ffmpeg only, no ffprobe)..."
  uv pip install --quiet --target "${SG_HOME}/py" imageio-ffmpeg
  local exe
  exe="$(PYTHONPATH="${SG_HOME}/py" python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
  ln -sf "${exe}" "${BIN}/ffmpeg"
}

if [ "${SLOPGUARD_FORCE_STATIC:-0}" = "1" ] || ! ffmpeg_ok; then
  install_static || install_imageio || {
    echo "Could not install ffmpeg. Set SLOPGUARD_FFMPEG to an ffmpeg binary and re-run." >&2
    exit 1
  }
fi

# Make the binaries callable as plain `ffmpeg` / `ffprobe` too: the assembly skill
# runs ffmpeg directly, not only through slopguard.
for b in ffmpeg ffprobe; do
  if ! have "${b}" && [ -x "${BIN}/${b}" ]; then ln -sf "${BIN}/${b}" "${HOME}/.local/bin/${b}"; fi
done

cat > "${HOME}/.local/bin/slopguard" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${HERE}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m slopguard "\$@"
EOF
chmod +x "${HOME}/.local/bin/slopguard"

case ":${PATH}:" in
  *":${HOME}/.local/bin:"*) ;;
  *) echo "note: add ${HOME}/.local/bin to PATH (Rakazo login shells already do)";;
esac

"${HOME}/.local/bin/slopguard" doctor
