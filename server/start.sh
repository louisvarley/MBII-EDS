#! /bin/bash

[ -z "$FS_GAME" ] && FS_GAME="base"

echo "Starting dedicated JA server with fs_game set as $FS_GAME"

/opt/ja-server/linuxjampded \
  +set dedicated 2 \
  +set fs_game "$FS_GAME" \
  +exec server.cfg
