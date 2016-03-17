#! /bin/bash

GAME_APP_PATH="/Volumes/Storage/SteamLibrary/steamapps/common/Jedi Academy/SWJKJA.app"
NET_PORT=29071
FS_GAME=base
SERVER_CFG=server.cfg

docker rm -f ja

docker run \
  -t=true \
  -d \
  --restart=always \
  --name ja \
  -v "$GAME_APP_PATH/Contents":"/jedi-academy" \
  -e NET_PORT="$NET_PORT" \
  -e FS_GAME="$FS_GAME" \
  -e SERVER_CFG="$SERVER_CFG" \
  --net=host \
  bsencan/jedi-academy-server
