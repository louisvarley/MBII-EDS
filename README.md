[![Docker Pulls](https://img.shields.io/docker/pulls/bsencan/jedi-academy-server.svg)](https://hub.docker.com/r/bsencan/jedi-academy-server/)
[![](https://images.microbadger.com/badges/image/bsencan/jedi-academy-server.svg)](https://microbadger.com/images/bsencan/jedi-academy-server "Get your own image badge on microbadger.com")
[![Gitter](https://img.shields.io/gitter/room/isair/jedi-academy-server.js.svg)](https://gitter.im/isair/jedi-academy-server)

The purpose of the project is to provide the JA community the means to set up scalable and solid servers, easily and quickly.

Table of Contents
---
1. [Usage](#usage)
2. [Stackfile Example](#stackfile-example)
3. [Development](#development)

Usage
---

Pull the image
```sh
docker pull bsencan/jedi-academy-server
```

Then run it
```sh
docker run \
  bsencan/jedi-academy-server \
  -v "PATH_TO_GAME_FILES":"/jedi-academy" \
  -e NET_PORT=YOUR_SERVER_PORT \
  -e FS_GAME=MOD_NAME \
  -e SERVER_CFG=CFG_FILE \
  -e RTVRTM_CFG=RTVRTM_CFG_FILE
```

All environment variables are optional. If not defined, `NET_PORT` defaults to 29070, `FS_GAME` defaults to `base`, and `SERVER_CFG` defaults to `server.cfg`, and `RTVRTM_CFG` defaults to blank (which means rtvrtm won't be initialized).

All your game and configuration files (e.g. `server.cfg`, `rtvrtm.cfg`, `maps.txt`, `base` and other folders with `pk3` files in them) must be in the path you'll replace `PATH_TO_GAME_FILES` with.

Stackfile Example
---

You can set up multiple servers in the blink of an eye on [Docker Cloud](https://cloud.docker.com/) using a Stackfile like the following.

```yml
ffa:
  image: bsencan/jedi-academy-server:latest
  restart: on-failure
  ports:
    - "29070:29070/udp"
  volumes:
    - PATH_TO_GAME_FILES:/jedi-academy
duels:
  image: bsencan/jedi-academy-server:latest
  restart: on-failure
  ports:
    - "29071:29070/udp"
  volumes:
    - PATH_TO_GAME_FILES:/jedi-academy
  environment:
    - SERVER_CFG=duel_server.cfg
mb2_duels:
  image: bsencan/jedi-academy-server:latest
  restart: on-failure
  ports:
    - "29072:29070/udp"
  volumes:
    - PATH_TO_GAME_FILES:/jedi-academy
  environment:
    - FS_GAME=MBII
    - SERVER_CFG=mb2_duel_server.cfg
    - RTVRTM_CFG=duel_rtvrtm.cfg
```

Development
---
If you cloned this repository and made changes to it, you can build a docker image by running `make`, and test it with `start-local-osx.sh`. You'll probably need to edit that script at the moment, but I'll make it more configurable later on.
