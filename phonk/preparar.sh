#!/usr/bin/env bash
# Phonk Hub: downloads SimpMusic at the pinned version, applies Phonk Hub's changes and its brand.
#
#   bash phonk/preparar.sh <destination folder> <build number>
#
# Run from the root of the Phonk Hub repository.
set -euo pipefail

DEST="${1:-app}"
BUILD_NUMBER="${2:-1}"
REPO_ROOT="$(pwd)"
source "$REPO_ROOT/phonk/version.env"

echo "SimpMusic $SIMPMUSIC_COMMIT, core $CORE_COMMIT, build $BUILD_NUMBER"
rm -rf "$DEST"
git clone --quiet --filter=blob:none https://github.com/maxrave-dev/SimpMusic.git "$DEST"
cd "$DEST"
git checkout --quiet "$SIMPMUSIC_COMMIT"
git submodule update --init --quiet
git -C core fetch --quiet origin "$CORE_COMMIT" || true
git -C core checkout --quiet "$CORE_COMMIT"

git apply --whitespace=nowarn "$REPO_ROOT/phonk/app.patch"
git -C core apply --whitespace=nowarn "$REPO_ROOT/phonk/core.patch"

# Every build gets a higher number, so phones and computers install it as an update.
sed -i "s/^version-name = .*/version-name = \"1.0.$BUILD_NUMBER\"/" gradle/libs.versions.toml
sed -i "s/^version-code = .*/version-code = \"$((100 + BUILD_NUMBER))\"/" gradle/libs.versions.toml
touch local.properties

python "$REPO_ROOT/phonk/aplicar_marca.py" . "$REPO_ROOT/marca" "${GITHUB_REPOSITORY:-}"
echo "Listo: $DEST"
