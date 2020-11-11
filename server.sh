#! /bin/bash

NAME="open"

CONFIG_DIRECTORY="/opt/openjk/configs"

# Names of File from (Found in /opt/openjk/configs)
SERVER_CONFIG="$NAME-server.cfg"
RTVRTM_CONFIG="$NAME-rtvrtm.cfg"
NET_PORT="29071"
NET_GAME="MBII"

#Remove any Instances of openjkded
docker rm -f openjkded

docker run \
  -t=true \
  --net=host \
  --name openjkded \
  -v "/opt/openjk/MBII":"/opt/openjk/MBII" \
  -v "/opt/openjk/base":"/opt/openjk/base" \
  -v "/opt/openjk/configs":"/opt/openjk/configs" \
  -e NET_PORT="$NET_PORT" \
  -e NET_GAME="$NET_GAME" \
  -e SERVER_CONFIG="$SERVER_CONFIG" \
  -e RTVRTM_CONFIG="$RTVRTM_CONFIG" \
  bsencan/jedi-academy-server


