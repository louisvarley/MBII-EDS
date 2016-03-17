#! /bin/bash

[ -z "$FS_GAME" ] && FS_GAME=base
[ -z "$SERVER_CFG" ] && SERVER_CFG=server.cfg

echo "Starting dedicated JA server from $SERVER_CFG (fs_game=$FS_GAME)"

mkdir -p /root/.ja/base
cp /jedi-academy/*.cfg /root/.ja/base

/opt/ja-server/linuxjampded \
  +set dedicated 2 \
  +set fs_game "$FS_GAME" \
  +exec "$SERVER_CFG"
