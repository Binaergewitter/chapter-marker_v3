#!/bin/sh
set -euf

#e.g. next:Binärgewitter/BGT289/local-ingo.flac

nextcloud_path=

if test -z "$nextcloud_path";then
  echo "finding bgt"
  today=$(curl https://pad.binaergewitter.de/ -v 2>&1 | sed -n 's/.*\/bgt\([0-9]\+\)\r/\1/p')
  nextcloud_path=next:Binärgewitter/BGT${today}/local.flac
  echo "using $nextcloud_path"
fi


front=$(echo $nextcloud_path | cut -d/ -f1)
show=$(echo $nextcloud_path | cut -d/ -f2)
fname=$(echo $nextcloud_path | cut -d/ -f 3)
local_fname="${show}_$fname"
local_chapters="${show}.chapters.txt" 
echo "!! Performing analysis for show $show with file $fname"

echo "4. transforming text to chapter-file"
python ./text2chapters.py "$@" "${show}.json"  | tee "$local_chapters" # --offset=15000 

