#!/bin/sh
# usage: ./copy_nextcloud (LOCAL_PATH [SHOWNUMBER]|NEXTCLOUD_PATH) 
#
# copies the input to BGT${SHOWNUMBER}_local.flac in the base directory
set -eufx
if test -f "${1:-}";then
  infile=$(readlink -f "${1:-}")
  today=${2:-$(curl https://pad.binaergewitter.de/ -v 2>&1 | sed -n 's/.*\/bgt\([0-9]\+\)\r/\1/p')}
  cd "$(dirname "$(readlink -f "$0")")"/..
  fname="BGT${today}_local.flac"
  cp "$infile" "BGT${today}_local.flac"
  echo "$fname"
else
  #e.g. next:Binärgewitter/BGT289/local-ingo.flac
  cd "$(dirname "$(readlink -f "$0")")"/..

  nextcloud_path=${1:-}

  if test -z "$nextcloud_path";then
    echo "finding bgt" >&2
    today=$(curl https://pad.binaergewitter.de/ -v 2>&1 | sed -n 's/.*\/bgt\([0-9]\+\)\r/\1/p')
    nextcloud_path=next:Binärgewitter/BGT${today}/local.flac
    echo "using $nextcloud_path" >&2
  fi


  # front=$(echo $nextcloud_path | cut -d/ -f1)
  if test -n "${2:-}";then
    show="BGT${2}"
  else
    show=$(echo $nextcloud_path | cut -d/ -f2)
  fi
  local_fname="${show}_local.flac"
  fname=$(echo $nextcloud_path | rev | cut -d/ -f1| rev)
  echo "!! Performing analysis for show $show with file $fname" >&2

  echo "1. copying $nextcloud_path to local dir" >&2
  if test -e "$local_fname" || test -n "${FORCE:-}" ;then
    echo "$local_fname already exists, not doing anything, use FORCE=true to copy anyway" >&2
  else
    until rclone copy -v "$nextcloud_path" . >&2;do
      echo "cannot find $nextcloud_path, retrying" >&2
      sleep 10
    done
    mv  "$fname" "$local_fname"
  fi
  echo "$local_fname"

fi

