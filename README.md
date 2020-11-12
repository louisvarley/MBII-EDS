
## New Republic Clan Docker Server Manager

Built for the **MBII New Republic Clan** 
This is a docker image and a helper python management program to run many server instances using quickly and easily.

This can be used as and where is needed.

## Introduction
This image is based on an older docker build by https://github.com/isair/jedi-academy-server
Some of the components including the use of the OG Engine needed an update. 

Image Changes so far is
- Ubuntu Based Image
- Using the MBII Dedicated OpenJK Server (more stable for MBII)

This package comes with a management file to make managing servers easier and quicker without the need to touch docker itself. 

The Provided python script acts as a "Mangement client" for the images. So you need no knowledge of docker to quickly spin up and manage servers. 

## Setup Requires

- Repo here is pulled and original Docker Image is pulled
- Run `make` within the directory to build the image and allow the server to use this altered build
- MBII (Linux) should be installed at /opt/openjk/MBII
- OpenJK files "should" be called at /opt/openjk/base (image does come with them but these act as a fall back)
- Original JA Base files also in /opt/openjk/base
- A folder in /opt/openjk/configs (See Configs)

Now you can run the python script MBII.py with the following arguements

## Instances
Instances are a single docker running a single MBII server. each instance has a instance name. This is normally one word refering to the server such as **open**

## Creating an Instance

All that is needed to create an instance, is a server.cfg and rtmrtv.cfg with named in the correct way to be added to the folder at `/opt/ojk2/configs`
named as such
`open-server.cfg`
`open-rtmrtv.cfg`

you should ensure your rtmrtv.cfg has the correct place holders. for example where the config uses a port. replace with [PORT]
When your instance starts, this will be replaced with the actual port number used automatically. 

more on naming configs below

## Actions against an instance
#### Usage

`-i [Name of your instance] ACTION`

Actions are run against an instance. 
Some examples. Where "instances" are called Open, Dueling and Cheats

`./MBII.py -i open start`

`./MBII.py -i dueling restart`

`./MBII.py -i cheats-on stop`

There a number of actions that can be used when specifying an "instance" 

#### start 
start an instance
#### stop
stop an instance
#### restart
restart an instance
#### status
show stats such as players, the map, uptime, port, ip 
#### ssh
Open a interactive SSH into the instance
#### exec
Run a shell command on the instance
#### log
Returns the entire server log from the instance 
*You can use > server.log to save this locally* 

### Vebose

When you run the start action if there was a problem, you may not know unless it was unable to find a given config file. You can view the output from the dedicated server directly by passing the `-v` arguement for Verbose mode. Pressing `Ctrl + c` will exit and the process will continue from then in non-verbose mode. 

### Still to do

Many things

- [x] Docks will auto restart the dedicated server if for any reason it fails. 
- [ ] Replace any references to PORT in config files with a place holder added by docker on launch
- [ ] Log can read extracted by an action
- [ ]  Make Python Management tool auto compile and be used as a binary 
- [ ]  Create an install.sh file to setup all directories download OpenJK and MBII
- [ ] Make management tool auto check for MBII updates and updates server
- [ ] Management tool to parse the server configs for info
- [ ] Wizard mode to create configs from scratch (maybe slightly gui)
- [ ] Inbuild discord bot connection thingy for external management
- [ ] Status action to show connected players
- [ ] Docks to auto reboot after 24 hours and when no players? maybe better than timed
- [ ] Management tool to expose RCON and SMOD
- [ ] Many more things probably


