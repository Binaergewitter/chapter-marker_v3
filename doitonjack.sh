#!/bin/sh
set -eufx

#e.g. next:Binärgewitter/BGT289/local-ingo.flac


fname=$(./helper/copy_nextcloud.sh "${1:-}")
show=${fname%%_local.flac}
front=next:Binärgewitter
chapters=$show.chapters.txt

echo "[*] copying $fname to jack"
rsync --progress "$fname" "sandro@jack:chapter-marker_v3/$fname"

echo "[*] performing sandro_doit.sh $fname"
time ssh sandro@jack nohup /home/sandro/chapter-marker_v3/sandro_doit.sh "$fname"


echo "[*] copying back $chapters"
scp "sandro@jack.r:chapter-marker_v3/$chapters" "$chapters"

echo "[*] copying $chapters to ${front}"
rclone copy "./$chapters" "${front}/${show}/"
