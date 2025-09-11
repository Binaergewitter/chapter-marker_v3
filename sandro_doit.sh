#!/usr/bin/env nix-shell
#!nix-shell shell.nix -i bash
set -euf

cd "$(dirname "$(readlink -f "$0")")"

# BGT353_local.flac

local_fname=$(basename "$1")
show=${local_fname%%_local.flac}
local_chapters="${show}.chapters.txt" 
echo "!! Performing analysis for show $show with file $local_fname" >&2

echo "2. splitting $local_fname" >&2
python ./split-voice.py "$local_fname" "$show" >&2

echo "3. performing stt with chunks" >&2
python ./chunks2text.py "${show}_chunks" | tee "${show}.json" >&2

echo "4. transforming text to chapter-file" >&2
python ./text2chapters.py "${show}.json" | tee "$local_chapters" >&2
echo "$local_chapters"
