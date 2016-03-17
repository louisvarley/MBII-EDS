Jedi Academy server solution without any headaches.

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
  -e FS_GAME="MOD_NAME" \
  -e SERVER_CFG="CFG_FILE"
```

The last two lines are optional. If not defined, `FS_GAME` defaults to `base` and `SERVER_CFG` default to `server.cfg`.

All your game files (e.g. `base` and other folders with `pk3` files in it) and `server.cfg` must be in the path you'll replace `PATH_TO_GAME_FILES` with.

Development
---
If you cloned this repository and made changes to it, you can build a docker image by running `make`, and test it with `start-local-osx.sh`. You'll probably need to edit that script at the moment, but I'll make it more configurable later on.
