#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--force] INPUT_IMAGE OUTPUT.png" >&2
}

force=0
if [[ "${1:-}" == "--force" ]]; then
  force=1
  shift
fi

if [[ "$#" -ne 2 ]]; then
  usage
  exit 2
fi

input=$1
output=$2

if [[ ! -f "$input" ]]; then
  echo "Input image not found: $input" >&2
  exit 1
fi

if [[ "$input" == "$output" ]]; then
  echo "Refusing to overwrite the input image." >&2
  exit 1
fi

if [[ "${output##*.}" != "png" && "${output##*.}" != "PNG" ]]; then
  echo "Output path must end in .png" >&2
  exit 1
fi

if [[ -e "$output" && "$force" -ne 1 ]]; then
  echo "Output already exists; choose a versioned name or pass --force: $output" >&2
  exit 1
fi

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick 'magick' is required." >&2
  exit 1
fi

output_dir=$(dirname "$output")
mkdir -p "$output_dir"
tmp=$(mktemp "$output_dir/.dy-ticket.XXXXXX.png")
trap 'rm -f "$tmp"' EXIT

magick "$input" \
  -filter Lanczos \
  -resize '1170x1560^' \
  -gravity center \
  -extent 1170x1560 \
  -alpha off \
  -strip \
  "$tmp"

dimensions=$(magick identify -format '%wx%h' "$tmp")
if [[ "$dimensions" != "1170x1560" ]]; then
  echo "Unexpected output dimensions: $dimensions" >&2
  exit 1
fi

mv "$tmp" "$output"
trap - EXIT
echo "$output"
