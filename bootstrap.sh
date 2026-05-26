#!/bin/sh
# Test Commander bootstrap.
# Verifies prereqs and auto-installs the safe ones (PDM via its official
# installer; git/make via apt on Linux/WSL). Does not install the project
# itself - run `make install` after this succeeds.
#
# POSIX shell. Idempotent. Never modifies PATH; never writes a make shim.

set -eu

info() { printf '[bootstrap] %s\n' "$*"; }
warn() { printf '[bootstrap] WARN: %s\n' "$*" >&2; }
err()  { printf '[bootstrap] ERROR: %s\n' "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

NEEDS_INSTALL=0
SUGGESTIONS=""
TC_PYTHON=""
PLATFORM=""

add_suggestion() {
    SUGGESTIONS="${SUGGESTIONS}  - ${1}
"
    NEEDS_INSTALL=1
}

apt_install() {
    pkg="$1"
    if have sudo && have apt-get; then
        info "${pkg}: installing via apt-get (may prompt for sudo)"
        sudo apt-get update -qq
        sudo apt-get install -y "$pkg"
    else
        add_suggestion "${pkg} (install via your platform package manager)"
    fi
}

detect_platform() {
    case "$(uname -s)" in
        Darwin)
            PLATFORM="macos" ;;
        Linux)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                PLATFORM="wsl"
            else
                PLATFORM="linux"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            PLATFORM="git-bash" ;;
        *)
            PLATFORM="unknown" ;;
    esac
    info "platform: ${PLATFORM}"
}

check_git() {
    if have git; then
        info "git: $(git --version 2>&1)"
        return 0
    fi
    case "${PLATFORM}" in
        linux|wsl)  apt_install git ;;
        macos)      add_suggestion "git (Xcode Command Line Tools: xcode-select --install)" ;;
        git-bash)   add_suggestion "git (re-install Git for Windows)" ;;
        *)          add_suggestion "git (install per your platform)" ;;
    esac
}

check_make() {
    if have make; then
        info "make: present"
        return 0
    fi
    case "${PLATFORM}" in
        linux|wsl)  apt_install make ;;
        macos)      add_suggestion "make (Xcode Command Line Tools: xcode-select --install)" ;;
        git-bash)   add_suggestion "make (choco install make, or switch to WSL)" ;;
        *)          add_suggestion "make (install per your platform)" ;;
    esac
}

check_python() {
    if have python3.12; then
        TC_PYTHON="python3.12"
    elif have python3; then
        ver=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "")
        case "${ver}" in
            3.12|3.13|3.14|3.15|3.16|3.17) TC_PYTHON="python3" ;;
        esac
    fi
    if [ -n "${TC_PYTHON}" ]; then
        info "python: $("${TC_PYTHON}" --version 2>&1)"
        return 0
    fi
    case "${PLATFORM}" in
        macos)
            add_suggestion "python 3.12 (brew install python@3.12)" ;;
        linux|wsl)
            add_suggestion "python 3.12 (sudo apt-get install python3.12 python3.12-venv, or pyenv install 3.12)" ;;
        git-bash)
            add_suggestion "python 3.12 (download from python.org, or switch to WSL)" ;;
        *)
            add_suggestion "python 3.12 (install per your platform)" ;;
    esac
}

check_pdm() {
    if have pdm; then
        info "pdm: $(pdm --version 2>&1 | head -1)"
        return 0
    fi
    if [ -z "${TC_PYTHON}" ]; then
        add_suggestion "pdm (install once Python 3.12 is present: curl -sSL https://pdm-project.org/install-pdm.py | python3 -)"
        return 0
    fi
    info "pdm: installing via the official PDM installer"
    curl -sSL https://pdm-project.org/install-pdm.py | "${TC_PYTHON}" -
    if have pdm; then
        info "pdm: $(pdm --version 2>&1 | head -1)"
    else
        warn "pdm installed but not on PATH (likely ~/.local/bin). Add it to PATH and re-run."
        add_suggestion "pdm (installed; add ~/.local/bin to your PATH)"
    fi
}

check_docker() {
    if have docker; then
        info "docker: $(docker --version 2>&1 | head -1)"
        return 0
    fi
    case "${PLATFORM}" in
        macos)
            add_suggestion "docker (choose: Docker Desktop, Colima [brew install colima], Rancher Desktop, or Podman with docker compat)" ;;
        linux|wsl)
            add_suggestion "docker (sudo apt-get install docker.io, or Docker Desktop, or Podman with docker compat)" ;;
        git-bash)
            add_suggestion "docker (Docker Desktop for Windows, or switch to WSL)" ;;
        *)
            add_suggestion "docker (install per your platform; any runtime with docker compat works)" ;;
    esac
}

usage() {
    cat <<EOF
Usage: bootstrap.sh [--help]

Verifies Test Commander prerequisites and auto-installs the safe ones
(PDM, and apt-managed make/git on Linux/WSL).

Auto-install policy:
  git       Linux/WSL via apt; macOS prompts Xcode CLI; Git Bash assumed present.
  make      Linux/WSL via apt; macOS prompts Xcode CLI; Git Bash prints install hint.
  python    Never auto-installed (users have strong opinions). Prints hint per platform.
  pdm       Auto-installed via the official installer once Python 3.12 is present.
  docker    Never auto-installed (runtime choice is yours). Prints choices per platform.

After this script succeeds, run: make install
EOF
}

case "${1:-}" in
    --help|-h)
        usage; exit 0 ;;
esac

info "Test Commander bootstrap starting"
detect_platform

check_git
check_make
check_python
check_pdm
check_docker

if [ "${NEEDS_INSTALL}" -ne 0 ]; then
    echo ""
    err "Some prerequisites are missing. Install:"
    printf '%s' "${SUGGESTIONS}"
    echo ""
    err "Re-run ./bootstrap.sh after installing."
    exit 1
fi

echo ""
info "All prerequisites present."
info "Next step: make install"
exit 0
