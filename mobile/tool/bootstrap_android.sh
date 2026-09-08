#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_LIB="$(mktemp -d)"
cp -R "$ROOT/lib" "$TMP_LIB/lib"
cp "$ROOT/pubspec.yaml" "$TMP_LIB/pubspec.yaml"

cd "$ROOT"
flutter create   --platforms=android   --org com.hastronventures   --project-name finpilot   .

rm -rf "$ROOT/lib"
cp -R "$TMP_LIB/lib" "$ROOT/lib"
cp "$TMP_LIB/pubspec.yaml" "$ROOT/pubspec.yaml"

echo "Android scaffold ready with package com.hastronventures.finpilot"
