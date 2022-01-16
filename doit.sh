#!/bin/sh
set -euf

#e.g. next:Binärgewitter/BGT289/local-ingo.flac
nexcloud_path=$1
front=$(echo $nexcloud_path | cut -d/ -f1)
show=$(echo $nexcloud_path | cut -d/ -f2)
fname=$(echo $nexcloud_path | cut -d/ -f 3)
local_fname="${show}_$fname"
local_chapters="${show}.chapters.txt" 
echo "!! Performing analysis for show $show with file $fname"

echo "1. copying $nexcloud_path to local dir"
rclone copy -v "$nexcloud_path" "."
mv -v "$fname" "$local_fname"

echo "2. splitting $fname"
python ./split-voice.py "$local_fname" "$show"

echo "3. performing stt with chunks"
python ./chunks2text.py "${show}_chunks" | tee "${show}.json"

echo "4. transforming text to chapter-file"
python ./text2chapters.py "${show}.json" | tee "$local_chapters" # --offset=15000 

echo "5. uploading chapters file to remote"
rclone copy "./$local_chapters" "${front}/${show}/"
