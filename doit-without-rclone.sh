#!/bin/sh
set -eufx

#e.g. next:Binärgewitter/BGT289/local-ingo.flac

nextcloud_path=$1
front="$(echo "$nextcloud_path" | cut -d/ -f1)"
show="$(echo "$nextcloud_path" | cut -d/ -f2)"
local_fname="${show}_local.flac"
fname=$(echo "$nextcloud_path" | rev | cut -d/ -f1| rev)

#./helper/copy_nextcloud.sh "$1"

echo "2. splitting $fname"
python ./split-voice.py "$local_fname" "$show"

echo "3. performing stt with chunks"
python ./chunks2text.py "${show}_chunks" | tee "${show}.json"

echo "4. transforming text to chapter-file"
python ./text2chapters.py "${show}.json" | tee "$local_chapters"

echo "5. uploading chapters file to remote"
rclone copy "./$local_chapters" "${front}/${show}/"
