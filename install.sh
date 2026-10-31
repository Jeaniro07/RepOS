#!/usr/bin/env bash
# One-command installer for the anti-slop video toolkit (Linux and macOS).
#
#   curl -fsSL https://raw.githubusercontent.com/Jeaniro07/RepOS/main/install.sh | bash
#
# Options (pass after `bash -s --` when piping):
#   --ref <branch|tag>   git ref to install (default: main)
#   --dir <path>         where to keep the repo (default: ~/antislop/RepOS)
#   --no-test            skip the self-test
#   --no-sudo            never use sudo; fail with instructions if a prerequisite is missing
#
# What it does: installs missing prerequisites (git, python3 >= 3.10, curl) with the system
# package manager (apt, dnf, yum, pacman, zypper, apk; Homebrew on macOS), clones or updates
# the repo, runs toolkit/setup.sh (static ffmpeg 8.1 into ~/.local/share/slopguard/bin, plus a
# `slopguard` command in ~/.local/bin), then runs `slopguard doctor` and the test suite.
# It never asks for or stores any API key.
set -euo pipefail

# Everything runs inside main(), called on the last line: when piped (curl | bash), bash then
# reads the whole script before any command runs, so no child process can swallow the rest of it.
main() {

  REF="main"
  DIR="${HOME}/antislop/RepOS"
  RUN_TESTS=1
  USE_SUDO=1
  REPO_URL="https://github.com/Jeaniro07/RepOS"

  while [ $# -gt 0 ]; do
    case "$1" in
      --ref) REF="$2"; shift 2 ;;
      --dir) DIR="$2"; shift 2 ;;
      --no-test) RUN_TESTS=0; shift ;;
      --no-sudo) USE_SUDO=0; shift ;;
      -h|--help) sed -n '2,18p' "$0" 2>/dev/null || true; exit 0 ;;
      *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
  done

  say() { printf '\n==> %s\n' "$*"; }
  have() { command -v "$1" >/dev/null 2>&1; }

  OS="$(uname -s)"
  SUDO=""
  if [ "$(id -u)" -ne 0 ] && [ "${USE_SUDO}" = 1 ] && have sudo; then SUDO="sudo"; fi

  python_ok() {
    local py
    for py in python3 python3.13 python3.12 python3.11 python3.10; do
      if have "${py}" && "${py}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PYTHON="${py}"
        return 0
      fi
    done
    return 1
  }

  install_pkgs() {
    # $@: logical names: git python curl
    local pkgs=() mgr=""
    if [ "${OS}" = "Darwin" ]; then
      if ! have brew; then
        echo "Homebrew is needed on macOS: https://brew.sh (then re-run this installer)." >&2
        exit 1
      fi
      for p in "$@"; do case "$p" in python) pkgs+=(python@3.12) ;; *) pkgs+=("$p") ;; esac; done
      brew install "${pkgs[@]}" </dev/null
      return
    fi
    if [ "$(id -u)" -ne 0 ] && [ -z "${SUDO}" ]; then
      echo "Missing: $*. Install them with your package manager (root needed), then re-run." >&2
      exit 1
    fi
    if have apt-get; then mgr=apt
    elif have dnf; then mgr=dnf
    elif have yum; then mgr=yum
    elif have pacman; then mgr=pacman
    elif have zypper; then mgr=zypper
    elif have apk; then mgr=apk
    else
      echo "No supported package manager found. Install: $* (python >= 3.10), then re-run." >&2
      exit 1
    fi
    for p in "$@"; do
      case "${mgr}:${p}" in
        apt:python) pkgs+=(python3) ;;
        dnf:python|yum:python|zypper:python|apk:python) pkgs+=(python3) ;;
        pacman:python) pkgs+=(python) ;;
        *) pkgs+=("$p") ;;
      esac
    done
    pkgs+=(ca-certificates)
    say "Installing ${pkgs[*]} with ${mgr}"
    case "${mgr}" in
      apt) ${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get update -y && ${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${pkgs[@]}" ;;
      dnf) ${SUDO} dnf install -y "${pkgs[@]}" ;;
      yum) ${SUDO} yum install -y "${pkgs[@]}" ;;
      pacman) ${SUDO} pacman -Sy --noconfirm --needed "${pkgs[@]}" ;;
      zypper) ${SUDO} zypper --non-interactive install "${pkgs[@]}" ;;
      apk) ${SUDO} apk add --no-cache "${pkgs[@]}" ;;
    esac
  }

  say "Checking prerequisites"
  missing=()
  have git || missing+=(git)
  have curl || missing+=(curl)
  python_ok || missing+=(python)
  if [ ${#missing[@]} -gt 0 ]; then
    install_pkgs "${missing[@]}"
    python_ok || { echo "Python 3.10+ is still missing after install." >&2; exit 1; }
  fi
  echo "git: $(git --version | cut -d' ' -f3)  python: $(${PYTHON} -c 'import platform; print(platform.python_version())')  os: ${OS} $(uname -m)"

  if [ "${OS}" = "Darwin" ] && ! have ffmpeg; then
    # setup.sh downloads static builds on Linux only; on macOS use Homebrew's ffmpeg.
    say "Installing ffmpeg with Homebrew"
    brew install ffmpeg </dev/null
  fi

  say "Getting ${REPO_URL} (${REF}) into ${DIR}"
  if [ -d "${DIR}/.git" ]; then
    git -C "${DIR}" fetch --depth 1 origin "${REF}" </dev/null
    git -C "${DIR}" checkout -q -B "${REF}" FETCH_HEAD </dev/null
  else
    mkdir -p "$(dirname "${DIR}")"
    git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${DIR}" </dev/null
  fi

  say "Setting up slopguard and ffmpeg"
  PATH="${HOME}/.local/bin:${PATH}" bash "${DIR}/toolkit/setup.sh" </dev/null

  if [ "${RUN_TESTS}" = 1 ]; then
    say "Self-test"
    (cd "${DIR}/toolkit" && PATH="${HOME}/.local/bin:${PATH}" "${PYTHON}" -m unittest discover -s tests </dev/null)
  fi

  case ":${PATH}:" in
    *":${HOME}/.local/bin:"*) path_note="" ;;
    *) path_note="Add ~/.local/bin to PATH (for example: echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc), then open a new terminal." ;;
  esac

  printf '\nDone. slopguard is installed.\n'
  printf '  Repo:     %s\n' "${DIR}"
  printf '  Try:      slopguard doctor\n'
  printf '            slopguard lint-script %s/examples/kopi-pahit/script-slop.md\n' "${DIR}"
  printf '  Rakazo:   Integrations > + > From GitHub > %s/tree/%s/rakazo-plugin\n' "${REPO_URL}" "${REF}"
  if [ -n "${path_note}" ]; then printf '%s\n' "${path_note}"; fi
}

main "$@"
