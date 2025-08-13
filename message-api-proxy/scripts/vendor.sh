#!/usr/bin/env bash
set -euo pipefail

# Generate lock file and requirements.txt
uv lock
uv export --no-dev --format requirements-txt -o .uv.requirements.txt

# Clean up existing dependencies and install to zip root
rm -rf _deps
mkdir -p _deps
uv pip install --python 3.12 --target ./_deps -r .uv.requirements.txt

# Copy dependencies to zip root
cp -a _deps/* ./

# Clean up temporary files
rm -rf _deps .uv.requirements.txt