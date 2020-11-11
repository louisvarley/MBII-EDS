#! /bin/bash

# Environment variables and their default values.
[ -z "$NET_PORT" ] && NET_PORT=29070
[ -z "$NET_GAME" ] && NET_GAME=base
[ -z "$RTVRTM_CONFIG" ] && RTVRTM_CONFIG=
[ -z "$SERVER_CONFIG" ] && SERVER_CONFIG=server.cfg

# Colors
RESTORE='\033[0m'
RED='\033[00;31m'
GREEN='\033[00;32m'
BLUE='\033[00;34m'

timestamp() {
  date +"%T" # current time
}

echo-green(){
  dt=`date '+%d/%m/%Y %H:%M:%S'`
  echo -e "${dt}: ${GREEN}${1}${RESTORE}"
}

echo-red(){
  dt=`date '+%d/%m/%Y %H:%M:%S'`
  echo -e "${dt}: ${RED}${1}${RESTORE}"
}

echo-blue(){
  dt=`date '+%d/%m/%Y_%H:%M:%S'`
  echo -e "${dt}: ${BLUE}${1}${RESTORE}"
}

echo-green "Starting $NET_GAME Dedicated Server..."

# Configuration files need to be under /root/.ja/base directory.

echo-green "Creating /root/.ja"
mkdir /root/.ja

echo-green "Creating /root/.ja/$NET_GAME"
mkdir /root/.ja/$NET_GAME

echo-green "Linking HOST $NET_GAME to /root/.ja/$NET_GAME"
ln -s "/root/.local/share/openjk/$NET_GAME" /root/.ja/$NET_GAME


if [ -f "/opt/openjk/configs/${SERVER_CONFIG}" ]; then
    echo-green "Copying HOST /opt/openjk/configs/${SERVER_CONFIG} to DOCKER /root/.ja/${NET_GAME}/${SERVER_CONFIG}"
    cp /opt/openjk/configs/$SERVER_CONFIG /root/.ja/$NET_GAME/$SERVER_CONFIG
else
    echo-red "Server Config on HOST at /opt/openjk/configs/${SERVER_CONFIG} Not Found. Cannot Continue..."
    exit 1
fi


# Shouldn't +set fs_game for base.
SET_FS_GAME="+set fs_game $NET_GAME"
if [ "$NET_GAME" = base ]; then
  SET_FS_GAME=""
fi

# If an rtvrtm configuration file has been defined and it exists, start rtvrtm.

if [ -f "/opt/openjk/configs/${RTVRTM_CONFIG}" ]; then
  echo-green "Found RTV RTM Config at /opt/openjk/configs/${RTVRTM_CONFIG}"

  cp /opt/openjk/MBII/*.txt /opt/rtvrtm
  cp "/opt/openjk/configs/${RTVRTM_CONFIG}" /opt/rtvrtm/rtvrtm.cfg

  echo-green "Starting RTV RTM Service for this $NET_GAME dedicated server"

  until (sleep 10; python /opt/rtvrtm/rtvrtm.py -c /opt/rtvrtm/rtvrtm.cfg --noupdate); do
    echo "RTVRTM crashed with exit code $?. Restarting..." >&2
  done &
else
  echo-red "Unable to find RTV RTM Config at /opt/openjk/configs/${RTVRTM_CONFIG}"
fi

cd /opt/openjk/


echo-green "Port $NET_PORT"

sleep 4

# Start the server.
openjkded \
  +set dedicated 2 \
  +set net_port "$NET_PORT" \
  +set fs_game MBII \
  +logfile 3
  +exec "$SERVER_CONFIG"
