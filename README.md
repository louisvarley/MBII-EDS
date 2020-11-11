## New Republic Clan Docker Server Manag

Built for the **MBII New Republic Clan** to run many server instances using docker
This can be used as and where is needed.

## Introduction
This script based on an older docker build by https://github.com/isair/jedi-academy-server
Some of the components including the use of the OG Engine needed an update. 

This package comes with a management file to make managing servers easier and quicker without the need to touch docker itself. 

## Setup Requires

- Repo here is pulled and original Docker Image is pulled
- Run `make` within the directory to build the image and allow the server to use this altered build
- MBII (Linux) should be installed at /opt/openjk/MBII
- OpenJK files "should" be called at /opt/openjk/base (image does some with them)
- Original JA Base files also in /opt/openjk/base
- A folder in /opt/openjk/configs (See Configs)

Now you can run the python script MBII.py with the following arguements

-n [Name of your instance]
-p [port]
-a [action]

Some examples. In this example the instance we are calling "open"

`./MBII.py -n open -a start -p 29072`

`./MBII.py -n open -a restart`

`./MBII.py -n open -a stop`

## Configs

Docker mounts your OpenJK Directory and looks for configs by matching your given instance name.
If your instance name you called in the MBII command was "open" it will look for
`open-server.cfg`
`open-rtvrtm.cfg`

So merely create these config files and leave in your config directory

if there is not rtvrtm.cfg file then Rock the Vote wont be started as a service within your docker. 

## Server logs

Server logs hide out on the docker itself at
`/root/.local/share/openjk/MBII/*NAME*-games.log`

### Still to do

Many things

- [ ] Replace any references to IP or PORT in config files with a place holder added by docker on launch
- [ ] Make logs accessable outside Docker by symlink them within MBII directory
- [ ]  Make Python Management tool auto compile and be used as a binary 
- [ ]  Create an install.sh file to setup all directories download OpenJK and MBII
- [ ] Make management tool auto check for MBII updates and updates server
- [ ] Management tool to parse the server configs for info
- [ ] Wizard mode to create configs from scratch (maybe slightly gui)
- [ ] Inbuild discord bot connection thingy for external management
- [ ] Status action to show connected players
- [ ] Docks to auto reboot after 24 hours and when no players? maybe better than timed
- [ ] Management tool to expose RCON and SMOD outside the dock (and for discord bot)
- [ ] Manegement tool to be able to stream in-game chatter outside the dock (and for discord bot)
- [ ] Many more things probably


