#! /bin/bash

GAME_APP_PATH="/Volumes/Storage/SteamLibrary/steamapps/common/Jedi Academy/SWJKJA.app"
FS_GAME="base"

docker rm -f ja

docker run \
  -t=true \
  -d \
  --restart=always \
  --name ja \
  -v "$GAME_APP_PATH/Contents":"/jedi-academy" \
  -e FS_GAME="$FS_GAME" \
  --net=host \
  bsencan/jedi-academy-server
