#!/usr/bin/env sh
set -eu
if command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
else
  echo "python or python3 is required" >&2
  exit 127
fi
UV_BIN=""
if command -v uv >/dev/null 2>&1; then
  UV_BIN=uv
elif [ -x "$HOME/.local/bin/uv" ]; then
  UV_BIN="$HOME/.local/bin/uv"
fi
if [ -n "$UV_BIN" ]; then
  export UV_BIN
  export UV_PROJECT_ENVIRONMENT=.venv-wsl
  export UV_LINK_MODE=copy
  "$UV_BIN" run "$PYTHON_BIN" scripts/run_verify.py "$@"
else
  # run_verify.py resolves uv itself and falls back to the current interpreter.
  "$PYTHON_BIN" scripts/run_verify.py "$@"
fi
