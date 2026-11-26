#!/bin/sh
# Install the built wheel into a clean venv and run an end-to-end round trip.
set -eu

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

python -m venv "$work/venv"
"$work/venv/bin/pip" install --quiet dist/*.whl

fs="$work/venv/bin/fsettings"
"$fs" --version

printf '%s\n' '{"theme": "dark", "trustedWorkspaces": []}' > "$work/template.json"
printf '%s\n' '{"model": "local", "trustedWorkspaces": ["/workspaces/example"]}' > "$work/target.json"

set +e
"$fs" "$work/template.json" "$work/target.json" > /dev/null
test $? -eq 1 || { echo "diff should exit 1 before push"; exit 1; }
set -e
"$fs" push "$work/template.json" "$work/target.json" > /dev/null
"$fs" "$work/template.json" "$work/target.json"
grep -q '"model": "local"' "$work/target.json"
grep -q '/workspaces/example' "$work/target.json"
"$fs" pull "$work/template.json" "$work/target.json" > /dev/null
"$fs" missing "$work/template.json" "$work/target.json" > /dev/null
python -m venv "$work/venv2"
"$work/venv2/bin/pip" install --quiet dist/*.whl
"$work/venv2/bin/python" -m frankensettings --version
echo "smoke ok"
