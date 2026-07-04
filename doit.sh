#!/bin/sh
set -euf

test -e .env && . ./.env
#e.g. next:Binärgewitter/BGT289/local-ingo.flac

# Parse arguments
force=0
nextcloud_path=""
for arg in "$@"; do
  case "$arg" in
    --force)argparse
      force=1
      ;;
    *)
      nextcloud_path="$arg"
      ;;
  esac
done

if test -z "$nextcloud_path";then
  echo "finding bgt"
  today=$(curl https://pad.binaergewitter.de/ -v 2>&1 | sed -n 's/.*\/bgt\([0-9]\+\)\r/\1/p')
  nextcloud_path=next:Binärgewitter/BGT${today}/local.flac
  echo "using $nextcloud_path"
fi

front=$(echo "$nextcloud_path" | cut -d/ -f1)
show=$(echo "$nextcloud_path" | cut -d/ -f2)
fname=$(echo "$nextcloud_path" | rev| cut -d/ -f 1| rev)
local_fname="${show}_$fname"
local_chapters="${show}.chapters.txt"
echo "!! Performing analysis for show $show with file $fname"

echo "1. copying $nextcloud_path to local dir"
if test -f "$local_fname" && test "$force" -eq 0; then
  echo "File $local_fname already exists, skipping download (use --force to override)"
else
  until rclone copy -v "$nextcloud_path" ".";do
    echo "cannot find $nextcloud_path, retrying"
    sleep 10
  done
  mv -v "$fname" "$local_fname"
fi

echo "2. splitting $fname"
python ./split-voice.py "$local_fname" "$show"

echo "3. performing stt with chunks"
python ./chunks2text.py "${show}_chunks" "${show}.json"

echo "4. transforming text to chapter-file"
python ./text2chapters.py "${show}.json" | tee "$local_chapters"

echo "5. uploading chapters file to remote"
rclone copy "./$local_chapters" "${front}/${show}/"
