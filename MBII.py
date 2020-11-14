#! bin/python -uSOO
import sys, getopt
import os
import subprocess
import docker
import re
import urllib2
import argparse
import json

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
    
    def __init__(self, name):
        self._DOCKER = docker.from_env()
        self._INSTANCE_NAME = name

    def exec_run(self, command):
        container = self._DOCKER.containers.list(all=True,filters={"name": self._INSTANCE_NAME})[0]
        stream = container.exec_run(command, stdout=True, stderr=True, stream=True)
        return stream

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
    def start(self, port, game, server_config_name, rtvrtm_config_name):
        if(not self.is_active() and not self.is_error()):

                print(bcolors.OK + "Starting Instance of " + game + " on port " + port + "..." + bcolors.ENDC)

                container = self._DOCKER.containers.create(
                    image='bsencan/jedi-academy-server',
                    name=self._INSTANCE_NAME,
                    stdin_open=True,
                    tty=True,
                    command='/bin/sh',
                    volumes=globals._VOLUME_BINDINGS,
                    network_mode ='host',
                    environment={"NET_PORT":port, "NET_GAME":game, "SERVER_CONFIG":server_config_name, "RTVRTM_CONFIG":rtvrtm_config_name}
                )    
                
                container.start()
                
                stream = container.exec_run("/opt/openjk/start.sh", stdout=globals._VERBOSE, stderr=globals._VERBOSE, stream=globals._VERBOSE)

                if(globals._VERBOSE):
                    for val in stream:
                        print (val)

    def ssh(self):
        os.system("docker exec -it " + self._INSTANCE_NAME + " bash")
        sys.exit(0)
        
    def read(self, path):  
        file_contents = self.exec_run("cat "+ path)
        return file_contents
             
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
    
    _RCON_CLIENT = None
    
    def __init__(self, name):
    
        self._NAME = name
        self._DOCKER_INSTANCE_NAME = "mbii-ded-" + name
        self._EXTERNAL_IP = urllib2.urlopen('http://ip.42.pl/raw').read()
        
        self._PRIMARY_MAP_PATH = globals._MB2_PATH + "/" + self._NAME + "-primary.txt"
        self._SECONDARY_MAP_PATH = globals._MB2_PATH + "/" + self._NAME + "-secondary.txt"
        
        self._CONFIG = self.get_config()
        
        self._PORT = str(self._CONFIG['server']['port'])
        self._HOST_NAME = self._CONFIG['server']['host_name']

        self._RCON_CLIENT = rcon_client(self._CONFIG['security']['rcon_password'], str(self._CONFIG['server']['port']))

        # server.CFG
        self._SERVER_CONFIG_NAME = self._NAME + "-server.cfg"
        self._SERVER_CONFIG_PATH = globals._MB2_PATH + "/" + self._SERVER_CONFIG_NAME
        
        # rtvrtm.CFG
        self._RTVRTM_CONFIG_NAME = self._NAME + "-rtvrtm.cfg"       
        self._RTVRTM_CONFIG_PATH = globals._MB2_PATH + "/" + self._RTVRTM_CONFIG_NAME    
        
        # games.log
        self._SERVER_LOG_NAME = self._NAME + "-games.log"
        self._SERVER_LOG_PATH = globals._DOCKER_BASE_PATH + "/" + self._SERVER_LOG_NAME
        
        self._DOCKER_INSTANCE = docker_instance(self._DOCKER_INSTANCE_NAME)
        
        # If instance running grab port
        if(self._DOCKER_INSTANCE.is_active()):
            self._PORT = self.get_port()
       
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
              
    def generate_rtvrtm_maps(self):
    
        if(self._CONFIG['server']['enable_rtv']):
            f = open(self._PRIMARY_MAP_PATH, "w")
            f.write("\n".join(self._CONFIG['primary_maps']))
            f.close()             
        
            f = open(self._SECONDARY_MAP_PATH, "w")
            f.write("\n".join(self._CONFIG['secondary_maps']))
            f.close()           
                       
    def get_config(self):
    
        config_file_path = globals._CONFIG_PATH + "/" + self._NAME + ".json"
        
        if(not os.path.isfile(config_file_path)):
            print(bcolors.FAIL + "An Instance named " + self._NAME + " was not found! in " + globals._CONFIG_PATH + bcolors.ENDC)
            exit()
    
        with open(config_file_path) as config_data:
            data = json.load(config_data)
            
        return data
       
    # Method to Grab the Port used by OpenJK Server by running netstat
    def get_port(self):  
        port = 0
        if(self._DOCKER_INSTANCE.is_active()):
            stream =  self._DOCKER_INSTANCE.exec_run("netstat -tulpn | grep mbiided")
            for val in stream:
                for item in val.split("\n"):
                    if "mbiided" in item:
                        port = item.split()[3].split(":")[1];   

            if(port > 0):
                return str(port)  

        return None  

    def get_rtv_status(self):  

        if(self._DOCKER_INSTANCE.is_active()):
            stream =  self._DOCKER_INSTANCE.exec_run('ps ax') #FYI Using Bars to merely return a 0 or 1 with GREP causing an error so doing parsing line by line here
            for val in stream:
                for item in val.split("\n"):
                    if("rtvrtm" in item):
                        return(True) 
                
        return False  

    def get_mbii_ded_status(self):  

        if(self._DOCKER_INSTANCE.is_active()):
            stream =  self._DOCKER_INSTANCE.exec_run('ps ax') #FYI Using Bars to merely return a 0 or 1 with GREP causing an error so doing parsing line by line here
            for val in stream:
                for item in val.split("\n"):
                    if("mbii" in item):
                        return(True) 
                
        return False  

    def rcon(self, command):
        self._RCON_CLIENT.send(str(command))
       
    def say(self, message):
        self._RCON_CLIENT.send("svsay " + message)
       
    def map(self, map_name):
         self._RCON_CLIENT.send("map " + map_name)       
       
    def mode(self, mode):   
          self._RCON_CLIENT.send("g_gametype " + mode)

    def kick(self, player):
        self._RCON_CLIENT.send("kick " + player)
        
    def ban(self, ip):
        self._RCON_CLIENT.send("addip " + ip)
        
    def unban(self, ip):
        self._RCON_CLIENT.send("removeip " + ip)
          
    def listbans(self):
        self._RCON_CLIENT.send("g_banips")
           
    # Start an Interactive SSH Instance
    def ssh(self):   
        self._DOCKER_INSTANCE.ssh()
            
    # Get list of players including IP and Ping using RCON
    def players(self):
        
        players = []
        status = self._RCON_CLIENT.send("status", True).title()
        status = status.split("\n") 
        
        x = 8
        while(x < len(status)):

            players.append(status[x].strip("  "))
            x = x + 1
            
        return players
        
    # Get list of players in server by parsing log    
    def players_using_log(self):
    
        players = {}
  
        stream = self._DOCKER_INSTANCE.read(self._SERVER_LOG_PATH)
  
        for val in stream:
        
            for line in val.split("\n"):

                line = helpers().fix_line(line)
                line_comp = line.strip(",").split()
                try: 
                    if(line_comp[1] == "ClientConnect:"):                  
                        line_tmp = line.split()   
                        player_name = line_comp[2].strip("()")
                        player_id = line_comp[4]
                        players[player_id] = player_name                     
                    if(line_comp[1] == "ClientDisconnect:"):     
                        try:
                            player_id = line_comp[2]
                            del players[player_id]
                        except KeyError:
                          pass                       
                        
                except IndexError:
                    pass
                                    
        return players
     
    # X Days Hs Ms Ss that server has been running using RCON
    def uptime(self):

        try:

            status = self._RCON_CLIENT.send("status", True).title()
            status = status.split("\n") 
            uptime = status[7].split(":")[1].lstrip(" ")

        except:
            uptime = "Error while fetching"
            
        return uptime 
 
    def log(self):
        stream = self._DOCKER_INSTANCE.read(self._SERVER_LOG_PATH)
        for val in stream:
            print(val)
 
    # Current Map using RCON
    def map(self):

        try:

            status = self._RCON_CLIENT.send("status", True).title()
            status = status.split("\n") 
            server_map = status[5].split(":")[1].lstrip(" ").lower().split(" ")[0]

        except:
            server_map = "Error while fetching"
            
        return server_map        
     
    # Start Instance
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
            self._DOCKER_INSTANCE.start(self._PORT, "MBII", self._SERVER_CONFIG_NAME, self._RTVRTM_CONFIG_NAME)

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
            
            if(self.get_mbii_ded_status()):   
                print(bcolors.CYAN + "Port: " + bcolors.ENDC + str(active_port))
                print(bcolors.CYAN + "Full Address: " + bcolors.ENDC + self._EXTERNAL_IP + ":" + str(active_port))
                print(bcolors.CYAN + "Map: " + bcolors.ENDC + self.map()) 
                print(bcolors.CYAN + "Uptime: " + bcolors.ENDC + self.uptime())
                
            print("-------------------------------------------") 
            
            if(self.get_mbii_ded_status()):               
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Dedicated Server Running")
            else:               
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "MBII Dedicated is Not active")           
            
            if(self.get_rtv_status()):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "RTV Service Running")            
            else:
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "RTV Service NOT Running")                       
          
            print("-------------------------------------------")   
                      
            if(self.get_mbii_ded_status()):             
                      
                print("Players ")
                
                players = self.players()
                
                for player in players:
                    print(bcolors().mbii_color(player) + bcolors.ENDC)

        elif(self._DOCKER_INSTANCE.is_error()):
            print("     " + bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance in failed state" + bcolors.ENDC)
     
        elif(not self._DOCKER_INSTANCE.is_error() and not self._DOCKER_INSTANCE.is_active()):     
             print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance not started" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + self._DOCKER_INSTANCE_NAME + " is currently in " + self._DOCKER_INSTANCE.status() + " state" + bcolors.ENDC) 

        print("-------------------------------------------")

    def stop(self):
    
        if(os.path.exists(self._SERVER_CONFIG_PATH)):
            os.remove(self._SERVER_CONFIG_PATH) 
                         
        if(os.path.exists(self._RTVRTM_CONFIG_PATH)):
            os.remove(self._RTVRTM_CONFIG_PATH) 
            
        self._DOCKER_INSTANCE.stop()

    def restart(self):     
        self.stop()
        self.start()           
                        
# Probably want to split instance manager and make an "instance" it's own class....
class instance_manager:

    # Instance now, different from the Docker Instance name (more friendly version)
    _NAME = None
    
    # Docker Instance name 
    _DOCKER_INSTANCE_NAME = None
    
    # External IP   
    _EXTERNAL_IP = None
    
    # Port is set either when instance started or fetched if already running
    _PORT = None
    _DOCKER_INSTANCE = None
    
    
    _SERVER_CONFIG_NAME = None
    _SERVER_CONFIG_PATH = None
    _RTVRTM_CONFIG_NAME = None
    _RTVRTM_CONFIG_PATH = None
    _SERVER_LOG_NAME = None
    _SERVER_LOG_PATH = None

    _MB2_PATH = "/opt/openjk/MBII"
    _BASE_PATH = "/opt/openjk/base"
    
    _MB2_MANAGER = None
    _OJK_MANAGER = None
    
    # Set Instance name and Get External IP
    def __init__(self):
        self._MB2_MANAGER = mb2_manager(self._MB2_PATH)
        self._OJK_MANAGER = ojk_manager(self._BASE_PATH)
        
    def get_instance(self, name):
        return server_instance(name)      

# Handles Checking Version of MB2, Updating, Downloading, Provisioning
class mb2_manager:
    
    _MB2_PATH = None    
        
    def __init__(self, mb2_path):
        self.__MB2_PATH = mb2_path
        
    def get_version(self):
        with open(self.__MB2_PATH + '/version.info', 'r') as file:
            data = file.read().replace('\n', '')
            
        return data
        
# Handles Checking Version of OJK, Updating, Downloading, Provisioning
class ojk_manager:

    BASE_PATH = None
    
    def __init__(self, base_path):
        self.BASE_PATH = base_path
        
    def get_version(self):
        with open(self.BASE_PATH + '/version.info', 'r') as file:
            data = file.read().replace('\n', '')
            
        return data        

class rcon_client:

    _RCON_PASSWORD = None
    _SERVER_PORT = None
    _CVAR = 0
    _HEAD = (chr(255) + chr(255) + chr(255) + chr(255))

    def __init__(self, rcon_password, server_port):
        self._RCON_PASSWORD = rcon_password
        self._SERVER_PORT = int(server_port)

    def send(self, command, quiet = False):
    
        reply = None
    
        try:
            if(not quiet):
                print("sending {}").format(command)
                
            msgFromClient       = "rcon {} {}".format(self._RCON_PASSWORD, command)
            bytesToSend         = str.encode(msgFromClient)
            serverAddressPort   = ("127.0.0.1", 29073)
            bufferSize          = 1024
            sock = socket(family=AF_INET, type=SOCK_DGRAM)
            socket.settimeout(sock, 4)
            sock.sendto(self._HEAD + bytesToSend, serverAddressPort)
            reply = sock.recvfrom(bufferSize)
            reply = reply[0][4:]         
            
            
        except(socket.timeout):
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
            
        _INSTANCE_MANAGER = instance_manager()    
            
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
        
        if(args.instance):
        
            if(len(args.instance) > 2):
                getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])(args.instance[2])
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