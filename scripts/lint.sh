#!/usr/bin/env bash

LINT_TMP="$(mktemp -t lint.XXXXXX)"
pycodestyle --exclude=venv > "$LINT_TMP"
if [ -s "$LINT_TMP" ]; then
    cat "$LINT_TMP"
    exit 1
else
    echo "No linting errors found."
fi
