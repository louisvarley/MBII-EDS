#!/usr/bin/python3

import sys, getopt
import os
import subprocess
import docker
import re
import urllib.request
import argparse
import json
import six
import binascii
import shlex
import psutil

from subprocess import Popen, PIPE, STDOUT

from socket import (socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SHUT_RDWR, gethostbyname_ex,
                    gaierror, timeout as socketTimeout, error as socketError)
 
# Holds Global Variables / Configs
class globals:

    _VERBOSE = False
    _SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
    _MB2_PATH = "/opt/openjk/MBII"
    _BASE_PATH = "/opt/openjk/base"
    _DOCKER_BASE_PATH = "/root/.local/share/openjk/MBII"
    _CONFIG_PATH = _SCRIPT_PATH + "/configs"
    _VOLUME_BINDINGS =   {
                            _MB2_PATH: {'bind': '/opt/openjk/MBII', 'mode': 'rw'}, 
                            _BASE_PATH: {'bind': '/opt/openjk/base', 'mode': 'ro'}, 
                            _CONFIG_PATH: {'bind': '/opt/openjk/configs', 'mode': 'ro'},              
                         }
                         
     
  
# Random Tools and Helpers
class helpers:

    def cvar_clean(self, text):
        return re.sub("\^[1-9]","",text)

    def fix_line(self, line):

      startswith = str.startswith
      split = str.split
      
      # Remove Any Spaces inside peoples usernames
      line = re.sub(r'\(.*?\)', lambda x: ''.join(x.group(0).split()), line)

      while startswith(line[8:], "Client "):

        line = split(line, ":", 3)

        if len(line) < 4: # If this bug is ever fixed within the MBII code,
                          # make sure this fix is not processed.
          return ""

        line[0] = int(line[0]) # Timestamp.

        for i in xrange(-1, -7, -1):

          substring = int(line[-2][i:])

          if (substring - line[0]) >= 0 or line[-2][(i-1)] == " ":

            line = "%3i:%s" % (substring, line[-1])
            break

      return line
     
# Static Class to hold Some Random Colours                        
class bcolors:

    #^1 - red 
    #^2 - green 
    #^3 - yellow 
    #^4 - blue 
    #^5 - cyan 
    #^6 - purple 
    #^7 - white 
    #^0 - black 
    #^9 - blank

    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    PURPLE = '\033[35m'
    WHITE = '\033[0m'
    BLACK = '\033[0m'
    
    def mbii_color(self, text):
    
        text = text.replace("^1", self.RED)
        text = text.replace("^2", self.GREEN)
        text = text.replace("^3", self.YELLOW)
        text = text.replace("^4", self.BLUE)
        text = text.replace("^5", self.CYAN)
        text = text.replace("^6", self.PURPLE)
        text = text.replace("^7", self.WHITE)
        text = text.replace("^0", self.BLACK)
        text = text.replace("^9", "")        
        return text
        
# An Instance of Docker
class docker_instance:

    # Probably could get these from Docker Library by NM
    _STATUS_RUNNING = "running"
    _STATUS_EXITED = "exited"
    _STATUS_NOT_FOUND = None
    
    # Will Hold the Docker Client Itself and Our Docker Instance Name
    _DOCKER = None
    _INSTANCE_NAME = None
    
    def __init__(self, instance):
        self._INSTANCE = instance
        self._DOCKER = docker.from_env()
        self._INSTANCE_NAME = self._INSTANCE._DOCKER_INSTANCE_NAME

    def exec(self, command):
        container = self._DOCKER.containers.list(all=True,filters={"name": self._INSTANCE_NAME})[0]
        stream = container.exec_run(command, stdout=True, stderr=True)
        return stream[1].decode()

    # Get Status of an Instance
    def status(self):
    
        if(self._DOCKER.containers.list(all=True,filters={"name": self._INSTANCE_NAME})):
            return self._DOCKER.containers.get(self._INSTANCE_NAME).status
        else:
            return self._STATUS_NOT_FOUND
               
    # Boolean, is this docker container running or not           
    def is_active(self):
        if(self.status() == self._STATUS_RUNNING):
            return True
        else:
           return False
           
    # Boolean, is this docker container has exited           
    def is_error(self):
        if(self.status() == self._STATUS_EXITED):
            return True
        else:
           return False           
        
    # Stop Instance    
    def stop(self):
    
        if(self._DOCKER.containers.list(all=True,filters={"name": self._INSTANCE_NAME})):
           print(bcolors.FAIL + "Stopping " + self._INSTANCE_NAME + " Instance..." + bcolors.ENDC)
           self._DOCKER.containers.get(self._INSTANCE_NAME).kill
           self._DOCKER.containers.get(self._INSTANCE_NAME).remove(force=True)
        else:
           print(bcolors.FAIL + "Instance " + self._INSTANCE_NAME + " not running..." + bcolors.ENDC)           

    # Start Instance
    def start(self):
    
        if(not self.is_active() and not self.is_error()):

                print(bcolors.OK + "Starting Instance of " + self._INSTANCE._CONFIG['server']['game'] + " on port " + self._INSTANCE._PORT + "..." + bcolors.ENDC)

                container = self._DOCKER.containers.create(
                    image='bsencan/jedi-academy-server',
                    name=self._INSTANCE_NAME,
                    stdin_open=True,
                    tty=True,
                    command='/bin/sh',
                    volumes=globals._VOLUME_BINDINGS,
                    network_mode ='host',
                    environment={"NET_RESTART_HOUR": self._INSTANCE._CONFIG['server']['schedule_restart_hour'],
                                 "NET_PORT":self._INSTANCE._PORT, 
                                 "NET_GAME":self._INSTANCE._CONFIG['server']['game'], 
                                 "SERVER_CONFIG":self._INSTANCE._SERVER_CONFIG_NAME, 
                                 "RTVRTM_CONFIG":self._INSTANCE._RTVRTM_CONFIG_NAME, 
                                 "SERVER_ENGINE": self._INSTANCE._CONFIG['server']['engine']
                                 }
                                                            )    
                
                container.start()
                
                exec_log = container.exec_run("/opt/openjk/start.sh", stdout=globals._VERBOSE, stderr=globals._VERBOSE, stream=globals._VERBOSE)
                
                for line in exec_log[1]:
                    print(line.decode())

    def ssh(self):
        os.system("docker exec -it " + self._INSTANCE_NAME + " bash")
        sys.exit(0)
        
    def read(self, path):  
        file_contents = self.exec("cat "+ path)
        return file_contents
        
    def ping_test(self, location, host):
        host = host.split(':')[0]
        cmd = "fping {host} -C 3 -q".format(host=host)
        # result = str(get_simple_cmd_output(cmd)).replace('\\','').split(':')[-1].split() if x != '-']
        result = self.exec(cmd)
        result = str(result).replace('\\', '').split(':')[-1].replace("n'", '').replace("-",'').replace("b''", '').split()
        res = [float(x) for x in result]
        if len(res) > 0:
            speed = round(sum(res) / len(res),2)
        else:
            speed = 999  

        print(location + ": " + str(round(speed,2)) + "ms")
             
# An Instance of MBII                        
class server_instance:

    _NAME = None
    _HOST_NAME = None
    _DOCKER_INSTANCE_NAME = None 
    _DOCKER_INSTANCE = None    
    _EXTERNAL_IP = None
    _PORT = None
    _PRIMARY_MAP_PATH = None
    _SECONDARY_MAP_PATH = None
    _SERVER_CONFIG_NAME = None
    _SERVER_CONFIG_PATH = None
    _RTVRTM_CONFIG_NAME = None
    _RTVRTM_CONFIG_PATH = None
    _SERVER_LOG_NAME = None
    _SERVER_LOG_PATH = None
    _UDP_CLIENT = None
    
    # Constructor
    def __init__(self, name):
    
        self._NAME = name
        self._DOCKER_INSTANCE_NAME = "mbii-ded-" + name
        self._EXTERNAL_IP = urllib.request.urlopen('http://ip.42.pl/raw').read().decode()
        
        
        self._PRIMARY_MAP_PATH = globals._MB2_PATH + "/" + self._NAME + "-primary.txt"
        self._SECONDARY_MAP_PATH = globals._MB2_PATH + "/" + self._NAME + "-secondary.txt"
        
        self._CONFIG = self.get_config()
        
        self._PORT = str(self._CONFIG['server']['port'])
        self._HOST_NAME = self._CONFIG['server']['host_name']

        self._UDP_CLIENT = udp_client(self._CONFIG['security']['rcon_password'], str(self._CONFIG['server']['port']))

        # server.CFG
        self._SERVER_CONFIG_NAME = self._NAME + "-server.cfg"
        self._SERVER_CONFIG_PATH = globals._MB2_PATH + "/" + self._SERVER_CONFIG_NAME
        
        # rtvrtm.CFG
        self._RTVRTM_CONFIG_NAME = self._NAME + "-rtvrtm.cfg"       
        self._RTVRTM_CONFIG_PATH = globals._MB2_PATH + "/" + self._RTVRTM_CONFIG_NAME    
        
        # games.log
        self._SERVER_LOG_NAME = self._NAME + "-games.log"
        self._SERVER_LOG_PATH = globals._DOCKER_BASE_PATH + "/" + self._SERVER_LOG_NAME
        
        self._DOCKER_INSTANCE = docker_instance(self)
        
        # If instance running grab port
        if(self._DOCKER_INSTANCE.is_active()):
            self._PORT = self.get_port()
       
    # Generate a server.cfg from JSON config   
    def generate_server_config(self):
        with open(globals._CONFIG_PATH + "/server.template", 'r') as file:
            data = file.read()
            
            # Server
            data = data.replace("[host_name]",self._CONFIG['server']['host_name'])
            data = data.replace("[discord]",self._CONFIG['server']['discord'])
            data = data.replace("[rcon_password]",self._CONFIG['security']['rcon_password'])
            data = data.replace("[log_name]",self._SERVER_LOG_NAME)
            
            # Messages
            data = data.replace("[message_of_the_day]",self._CONFIG['messages']['message_of_the_day'].replace("\n","\\n"))
            
            # Game
            data = data.replace("[server_password]",self._CONFIG['security']['server_password'])
            data = data.replace("[map_win_limit]",str(self._CONFIG['game']['map_win_limit']))
            data = data.replace("[map_round_limit]",str(self._CONFIG['game']['map_round_limit']))
            data = data.replace("[balance_mode]",str(self._CONFIG['game']['balance_mode']))
            data = data.replace("[competitive_config]",str(self._CONFIG['game']['competitive_config']))
            
            # Admin
            data = data.replace("[admin_1_password]",self._CONFIG['smod']['admin_1']['password']) 
            data = data.replace("[admin_1_config]",str(self._CONFIG['smod']['admin_1']['config']))
            
            data = data.replace("[admin_2_password]",self._CONFIG['smod']['admin_2']['password']) 
            data = data.replace("[admin_2_config]",str(self._CONFIG['smod']['admin_2']['config']))
            
            data = data.replace("[admin_3_password]",self._CONFIG['smod']['admin_3']['password']) 
            data = data.replace("[admin_3_config]",str(self._CONFIG['smod']['admin_3']['config']))   
            
            data = data.replace("[admin_4_password]",self._CONFIG['smod']['admin_4']['password']) 
            data = data.replace("[admin_4_config]",str(self._CONFIG['smod']['admin_4']['config']))
            
            data = data.replace("[admin_5_password]",self._CONFIG['smod']['admin_5']['password']) 
            data = data.replace("[admin_5_config]",str(self._CONFIG['smod']['admin_5']['config']))
            
            data = data.replace("[admin_6_password]",self._CONFIG['smod']['admin_6']['password']) 
            data = data.replace("[admin_6_config]",str(self._CONFIG['smod']['admin_6']['config']))
            
            data = data.replace("[admin_7_password]",self._CONFIG['smod']['admin_7']['password']) 
            data = data.replace("[admin_7_config]",str(self._CONFIG['smod']['admin_7']['config']))
            
            data = data.replace("[admin_8_password]",self._CONFIG['smod']['admin_8']['password']) 
            data = data.replace("[admin_8_config]",str(self._CONFIG['smod']['admin_8']['config']))
            
            data = data.replace("[admin_9_password]",self._CONFIG['smod']['admin_9']['password']) 
            data = data.replace("[admin_9_config]",str(self._CONFIG['smod']['admin_9']['config']))
            
            data = data.replace("[admin_10_password]",self._CONFIG['smod']['admin_10']['password']) 
            data = data.replace("[admin_10_config]",str(self._CONFIG['smod']['admin_10']['config']))

            # Maps
 
 
            data = data.replace("[map_1]",self._CONFIG['map_rotation_order'][0])
            data = data.replace("[map_2]",self._CONFIG['map_rotation_order'][1])
            data = data.replace("[map_3]",self._CONFIG['map_rotation_order'][2])
            data = data.replace("[map_4]",self._CONFIG['map_rotation_order'][3])
            data = data.replace("[map_5]",self._CONFIG['map_rotation_order'][4])
            data = data.replace("[map_6]",self._CONFIG['map_rotation_order'][5])
            data = data.replace("[map_7]",self._CONFIG['map_rotation_order'][6])
            data = data.replace("[map_8]",self._CONFIG['map_rotation_order'][7])
            data = data.replace("[map_9]",self._CONFIG['map_rotation_order'][8])
            
            # 0 = Open mode, 1 = Semi-Authentic, 2 = Full-Authentic, 3 = Duel, 4 = Legends
            
            # Mode
            
            if(self._CONFIG['game']['mode'].lower() == "open"):
                data = data.replace("[mode]","0")   
                
            if(self._CONFIG['game']['mode'].lower() == "semi-authentic"):
                data = data.replace("[mode]","1") 
                
            if(self._CONFIG['game']['mode'].lower() == "full-authentic"):
                data = data.replace("[mode]","2") 
                
            if(self._CONFIG['game']['mode'].lower() == "duel"):
                data = data.replace("[mode]","3") 
                
            if(self._CONFIG['game']['mode'].lower() == "legends"):
                data = data.replace("[mode]","4")    

            # Default if no matches were made
            data = data.replace("[mode]","0")                
            
            # Class Limits
            cl_string = ""
            for x in self._CONFIG['class_limits']:
                limit = self._CONFIG['class_limits'][x]
                if(limit < 10):
                    limit = "0" + str(limit)
                    
                cl_string = cl_string + str(limit) + "-"
                
            cl_string = cl_string.rstrip("-")
            data = data.replace("[class_limits]",cl_string)
            
            # Save to MBII Folder
            f = open(self._SERVER_CONFIG_PATH, "w")
            f.write(data)
            f.close()

    # Generate an RTV RTM Config from JSON config
    def generate_rtvrtm_config(self):
    
        if(self._CONFIG['server']['enable_rtv'] or self._CONFIG['server']['enable_rtm']):
    
            with open(globals._CONFIG_PATH + "/rtvrtm.template", 'r') as file:
                data = file.read()
                data = data.replace("[log_path]",self._SERVER_LOG_PATH)
                data = data.replace("[rcon_password]",self._CONFIG['security']['rcon_password'])          
                data = data.replace("[primary_maps_path]",  self._PRIMARY_MAP_PATH)    
                data = data.replace("[secondary_maps_path]", self._SECONDARY_MAP_PATH)            
                data = data.replace("[mbii_path]",globals._MB2_PATH)           
                data = data.replace("[port]",str(self._CONFIG['server']['port']))  

                if(self._CONFIG['server']['enable_rtv']):
                    data = data.replace("[rtv_mode]","1")  
                else:
                    data = data.replace("[rtv_mode]","0")  
 
                if(self._CONFIG['server']['enable_rtm']):
                    data = data.replace("[rtm_mode]",str(self._CONFIG['server']['rtm_mode'])) 
                else:
                    data = data.replace("[rtm_mode]","0")                     
                    
            f = open(self._RTVRTM_CONFIG_PATH, "w")
            f.write(data)
            f.close()    
       
    # Generate RTV RTM Maps List from JSON config
    def generate_rtvrtm_maps(self):
    
        if(self._CONFIG['server']['enable_rtv']):
            f = open(self._PRIMARY_MAP_PATH, "w")
            f.write("\n".join(self._CONFIG['primary_maps']))
            f.close()             
        
            f = open(self._SECONDARY_MAP_PATH, "w")
            f.write("\n".join(self._CONFIG['secondary_maps']))
            f.close()           
      
    # Fetch config JSON to dictionary
    def get_config(self):
    
        config_file_path = globals._CONFIG_PATH + "/" + self._NAME + ".json"
        
        if(not os.path.isfile(config_file_path)):
            print(bcolors.FAIL + "An Instance named " + self._NAME + " was not found! in " + globals._CONFIG_PATH + bcolors.ENDC)
            exit()
    
        with open(config_file_path) as config_data:
            data = json.load(config_data)
            
        return data
       
    # Use netstat to get the port used by this instance
    def get_port(self):  
        port = 0
        if(self._DOCKER_INSTANCE.is_active()):
            response =  self._DOCKER_INSTANCE.exec("netstat -tulpn | grep mbiided")
            for item in response.splitlines():
                if "mbiided" in item:
                    port = item.split()[3].split(":")[1];   

            if(int(port) > 0):
                return str(port)  

        return None  

    # Is RTV / RTM Service running and instance
    def get_rtv_status(self):  

        if(self._DOCKER_INSTANCE.is_active()):
            response =  self._DOCKER_INSTANCE.exec('ps ax') #FYI Using Bars to merely return a 0 or 1 with GREP causing an error so doing parsing line by line here
            for item in response.splitlines():
                if("rtvrtm" in item):
                    return(True) 
                
        return False  

    # Is the chosen engine running an instance
    def get_ded_engine_status(self):  

        if(self._DOCKER_INSTANCE.is_active()):
            response =  self._DOCKER_INSTANCE.exec('ps ax') #FYI Using Bars to merely return a 0 or 1 with GREP causing an error so doing parsing line by line here
            for item in response.splitlines():
                if(self._CONFIG['server']['engine'] in item):
                    return(True) 
                
        return False  

    # Run an RCON command
    def rcon(self, command):
        return self._UDP_CLIENT.send(str(command))
       
    # Run a console command
    def cmd(self, command):
        return self._UDP_CLIENT.cmd(command, True)       
       
    # Get / Set a CVAR
    def cvar(self, key, value = None):
    
        if(value == None): # GET a CVAR Value
            response = self._UDP_CLIENT.rcon(key,True)
            try:
                response = re.findall(r'"([^"]*)"', response)[0]
                result = helpers().cvar_clean(response)
                
            except:    
                print("Error, unknown or invalid cvar")

            return result
        
        else: #SET a CVAR Value
            response = self._UDP_CLIENT.rcon("set " + key + "=" + str(value))            
       
    # Run an SVSAY command
    def say(self, message):
        self._UDP_CLIENT.send("svsay " + message)
       
    # Get / Set current map
    def map(self, map_name = None):
    
         if(not map_name == None):
            self._UDP_CLIENT.rcon("map " + map_name, True)
            return True
         else:
            try:
                server_map = self.cvar("mapname")
               
            except:
                server_map = "Error while fetching"
            
            return server_map        
        
    # Get / Set current mode
    def mode(self, mode = None):   

         if(not mode == None):
            self.cvar("g_Authenticity", mode)
            return True
         else:
            try:
                mode = self.cvar("g_Authenticity", None).strip()
                #0 = Open mode, 1 = Semi-Authentic, 2 = Full-Authentic, 3 = Duel, 4 = Legends
                if(mode == "0"):
                    return "Open"
                if(mode == "1"):
                    return "Semi-Authentic"
                if(mode == "2"):
                    return "Full-Authentic"
                if(mode == "3"):
                    return "Duel"
                if(mode == "4"):                
                    return "Legends"     
                        
            except:
               mode = "Error while fetching"
            
            return mode  

    # Server uptime as a string
    def uptime(self):

        #try:

        status = self._UDP_CLIENT.rcon("status", True).title()
        status = status.split("\n") 
        uptime = status[7].split(":")[1].lstrip(" ")

        #except:
         #   uptime = "Error while fetching"
            
        return uptime 
 
    # Kick a player
    def kick(self, player):
        self._UDP_CLIENT.send("kick " + player)
        
    # Ban a player    
    def ban(self, ip):
        self._UDP_CLIENT.send("addip " + ip)
       
    # Unban a player
    def unban(self, ip):
        self._UDP_CLIENT.send("removeip " + ip)
       
    # List banned players
    def listbans(self):
        self._UDP_CLIENT.send("g_banips")
           
    # Start an Interactive SSH Instance
    def ssh(self):   
        self._DOCKER_INSTANCE.ssh()
            
    # Int of the number of players in game        
    def players_count(self):
        return len(self.players())
            
    # Get list of players in game
    def players(self):
        
        players = []
        status = self.cmd("getstatus")
        status = status.split("\n")
        
        x = 2
        while(x < int(len(status)-1)):
            line = str(status[x])
            line_split = shlex.split(line)
            player = line_split[2]
            players.append(player)
            x = x + 1
            
        return players
        
    # Print the server log
    def log(self):
        stream = self._DOCKER_INSTANCE.read(self._SERVER_LOG_PATH)
        for val in stream:
            print(val)
 
    # Run an automated test on a number of things printing results
    def test(self):
    
        response = urllib.request.urlopen('http://ipinfo.io/json')
        lookup = json.load(response)
        print("Testing from {} {}".format(self._EXTERNAL_IP, lookup['region']))
        print("-------------------------------------------")
        self._DOCKER_INSTANCE.ping_test("CA Central", "35.182.0.251")    
        self._DOCKER_INSTANCE.ping_test("EU East", "35.178.0.253")
        self._DOCKER_INSTANCE.ping_test("EU Central", "18.196.0.253")
        self._DOCKER_INSTANCE.ping_test("EU West", "34.240.0.253")
        self._DOCKER_INSTANCE.ping_test("US WEST", "52.52.63.252")
        self._DOCKER_INSTANCE.ping_test("US EAST", "35.153.128.254")
        print("-------------------------------------------")
        print("CPU Usage: {}%".format(str(psutil.cpu_percent())))
        print("Memory Usage: {}%".format(str(psutil.virtual_memory().percent)))       
         
    # Start this instance
    def start(self):

        self.generate_server_config()
        self.generate_rtvrtm_config()
        self.generate_rtvrtm_maps()
        
        # Instance Running
        if(self._DOCKER_INSTANCE.is_active()):
            print(bcolors.OK + "Instance is already running..." + bcolors.ENDC)  
            return
            
        # Instance Needs Restart    
        if(self._DOCKER_INSTANCE.is_error()):
            print(bcolors.FAIL + "Instance Had Exited, Restarting..." + bcolors.ENDC)
            self._DOCKER_INSTANCE.stop()
        
        # Instance Can Start

        if(os.path.exists(self._SERVER_CONFIG_PATH)):
            print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Loaded SERVER config")
                         
            if(os.path.exists(self._RTVRTM_CONFIG_PATH)):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Loaded RTVRTM config")
                
                if(self._CONFIG['server']['enable_rtv']):
                    print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Enable Rock the Vote")               
                else:
                    print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Enable Rock the Vote")              
                if(self._CONFIG['server']['enable_rtm']):
                    print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Enable Rock the Mode")               
                else:
                    print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Enable Rock the Mode")                 
                
            else:
            
                if(self._CONFIG['server']['enable_rtv'] or self._CONFIG['server']['enable_rtm']):
                    print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Unable to Load RTVRTM config at " +  self._RTVRTM_CONFIG_PATH + bcolors.ENDC)                             
                    
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Enable Rock the Vote")   
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Enable Rock the Mode")   

            print("-------------------------------------------")
            i = self._CONFIG
            self._DOCKER_INSTANCE.start()
            #self._CONFIG, game="MBII",port=self._PORT,config_name=self._SERVER_CONFIG_NAME,rtvrtm_config_name=self._RTVRTM_CONFIG_NAME)
        else:
            print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Unable to Load SERVER config at " + self._SERVER_CONFIG_PATH)
            print(bcolors.FAIL + "Unable to proceed without a valid Server Config File" + bcolors.ENDC)
            exit()

    # Instance Status Information
    def status(self):

        print("-------------------------------------------")
        if(self._DOCKER_INSTANCE.is_active()):
        
            active_port = self.get_port()
            print(bcolors.CYAN + "Docker Instance: " + bcolors.ENDC + self._DOCKER_INSTANCE_NAME)
            print(bcolors.CYAN + "Server Name: " + bcolors.ENDC + bcolors().mbii_color(self._CONFIG['server']['host_name']))
            
            if(self.get_ded_engine_status()):   
                print(bcolors.CYAN + "Port: " + bcolors.ENDC + str(active_port))
                print(bcolors.CYAN + "Mod: " + bcolors.ENDC + str(self._CONFIG['server']['game']))
                print(bcolors.CYAN + "Engine: " + bcolors.ENDC + str(self._CONFIG['server']['engine']))                
                print(bcolors.CYAN + "Full Address: " + bcolors.ENDC + self._EXTERNAL_IP + ":" + str(active_port))
                print(bcolors.CYAN + "Map: " + bcolors.ENDC + self.map(None)) 
                print(bcolors.CYAN + "Mode: " + bcolors.ENDC + self.mode(None))                 
                print(bcolors.CYAN + "Uptime: " + bcolors.ENDC + self.uptime())
                
            print("-------------------------------------------") 
            
            if(self.get_ded_engine_status()):               
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Dedicated Server Running")
            else:               
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "MBII Dedicated is Not active")           
            
            if(self.get_rtv_status()):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "RTV Service Running")            
            else:
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "RTV Service NOT Running")                       
          
            print("-------------------------------------------")   
                      
            if(self.get_ded_engine_status()):             
                      
                print("Players ")
                
                players = self.players()
                
                if(len(players) > 0):
                
                    for player in players:
                        print(bcolors().mbii_color(player) + bcolors.ENDC)
                else:
                    print(bcolors.FAIL + "No one is playing"  + bcolors.ENDC )

        elif(self._DOCKER_INSTANCE.is_error()):
            print("     " + bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance in failed state" + bcolors.ENDC)
     
        elif(not self._DOCKER_INSTANCE.is_error() and not self._DOCKER_INSTANCE.is_active()):     
             print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance not started" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + self._DOCKER_INSTANCE_NAME + " is currently in " + self._DOCKER_INSTANCE.status() + " state" + bcolors.ENDC) 

        print("-------------------------------------------")

    # Stop the instance
    def stop(self):
    
        if(os.path.exists(self._SERVER_CONFIG_PATH)):
            os.remove(self._SERVER_CONFIG_PATH) 
                         
        if(os.path.exists(self._RTVRTM_CONFIG_PATH)):
            os.remove(self._RTVRTM_CONFIG_PATH) 
            
        self._DOCKER_INSTANCE.stop()

    # Stop then start the instance
    def restart(self):     
        self.stop()
        self.start()           
                        
# Instance manager is used to setup and get instances
class manager:

    _MB2_PATH = "/opt/openjk/MBII"
    _MB2_MANAGER = None

    # Set Instance name and Get External IP
    def __init__(self):
        self._MB2_MANAGER = mb2_manager(self._MB2_PATH)
        
    def get_instance(self, name):
        return server_instance(name)      
        
    def list(self):
        config_file_path = globals._CONFIG_PATH
        for filename in os.listdir(config_file_path):
            if(filename.endswith(".json")):
                print(filename.replace(".json",""))

# Handles Checking Version of MB2, Updating, Downloading, Provisioning
class mb2_manager:
    
    _MB2_PATH = None    
        
    def __init__(self, mb2_path):
        self.__MB2_PATH = mb2_path
        
    def get_version(self):
        with open(self.__MB2_PATH + '/version.info', 'r') as file:
            data = file.read().replace('\n', '')
            
        return data
        
# Client for Handling RCON, SMOD and RAW server UDP Commands  
class udp_client:

    _RCON_PASSWORD = None
    _SERVER_PORT = None
    _CVAR = 0
    _HEAD = (chr(255) + chr(255) + chr(255) + chr(255))

    def __init__(self, rcon_password, server_port):
        self._RCON_PASSWORD = rcon_password
        self._SERVER_PORT = int(server_port)
      
    def rcon(self, command, quiet = False):
    
        reply = None
    
        try:
            if(not quiet):
                print("Sent:{}".format(command))
                
            send_command       = (self._HEAD + "rcon {} {}".format(self._RCON_PASSWORD, command))
            serverAddressPort   = ("127.0.0.1", self._SERVER_PORT)
            bufferSize          = 1024
            sock = socket(family=AF_INET, type=SOCK_DGRAM)
            socket.settimeout(sock, 4)           
            sock.sendto(six.b(send_command), serverAddressPort)
            reply = sock.recvfrom(bufferSize)
            reply = reply[0][4:].decode()             
         
        except:
            print("Unable to connect to server RCON")
            
        finally:
            sock.close()

        if reply.startswith("print\nbad rconpassword"):
            print("Incorrect rcon password.")               

        elif(reply.startswith("disconnect")):
            print("got a disconnect response")               

        elif not reply.startswith("print"):
            print("Unexpected error while contacting server for the first time.")

        if(not quiet):
            print("Reply:{}".format(reply))
            
        return reply

    def cmd(self, command, quiet = False):
    
        reply = None
    
        try:
            if(not quiet):
                print("Sent:{}".format(command))
                
            send_command       = (self._HEAD + "{}".format(command))
            serverAddressPort   = ("127.0.0.1", self._SERVER_PORT)
            bufferSize          = 1024
            sock = socket(family=AF_INET, type=SOCK_DGRAM)
            socket.settimeout(sock, 4)           
            sock.sendto(six.b(send_command), serverAddressPort)
            reply = sock.recvfrom(bufferSize)
            reply = reply[0][4:].decode()             
         
        except:
            print("Unable to connect to server")
            
        finally:
            sock.close()   

        if(reply == None):
            return "No Response"

        elif(reply.startswith("disconnect")):
            print("got a disconnect response")               

        if(not quiet):
            print("Reply:{}".format(reply))
            
        return reply    

# Main Class
class main:

    _INSTANCE_MANAGER = None
    _VERBOSE = False
    _PORT = None

    # Usage Banner
    def usage(self):
        print("usage: MBII [OPTIONS]")
        print("")
        print("Option                                    Name            Meaning")
        print("-i <instance> [command] [optional args]   Instance        Use to run commands against a named instance")  
        print("-l                                        List            List all Instances available")        
        print("-u                                        Update          Check for MBII Updates, Update when ALL instances are empty")
        print("-v                                        Verbose         Enable verbose mode")          
        print("-h                                        Help            Show this help screen")  
        
        print("")
        
        print("Instance Commands")
        print("Option             Description")
        print("Start              Start Instance")
        print("Stop               Stop Instance") 
        print("Restart            Restart Instance") 
        print("Status             Instance Status") 
        print("rcon               Issue RCON Command In Argument") 
        print("smod               Issue SMOD Command In Argument")         

        
        exit()

    # Main Function
    def main(self,argv):
    
        if(len(sys.argv) == 1):
            self.usage()
            
        _INSTANCE_MANAGER = manager()    
            
        parser = argparse.ArgumentParser(add_help=False)
        
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-i", type=str, help="Action on Instance", nargs="+", metavar=('INSTANCE', 'ACTION', 'OPTIONAL_ARGS'), dest="instance")   
        group.add_argument("-l", action="store_true", help="List Instances", dest="list")            
        group.add_argument("-u", action="store_true", help="Update MBII", dest="update")    
        group.add_argument("-h", action="store_true", help="Help Usage", dest="help")  
        parser.add_argument("-v", action="store_true", help="Verbosed Output", dest="verbose")   
        
        args = parser.parse_args()
        
        if(args.verbose):
            globals._VERBOSE = True
            
        if(args.help):
            self.usage()
            exit()
            
        if(args.list):
            _INSTANCE_MANAGER.list()
            exit()
            
        
        if(args.instance):
        
            if(len(args.instance) == 3):
                getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])(args.instance[2])
            elif(len(args.instance) == 4):
                 getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])(args.instance[2], args.instance[3])           
            else:
                getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])()
        
            #try:
                #getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])()
                
            #except:
                #print("Invalid Command " + args.instance[1]) 
        
        elif(args.list): 
            _INSTANCE_MANAGER.list()

        elif(args.update):
            _INSTANCE_MANAGER.update()
        
if __name__ == "__main__":
   main().main(sys.argv[1:])
