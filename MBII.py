#! bin/python
import sys, getopt
import os
import subprocess
import docker
import re
import urllib2
import argparse

# Various Configs left here so they are accessable

#GLOBALS
NAME = None
MODE = None
PORT = None
ACTION = None
VERBOSE = False
INSTANCE_NAME = None

#DOCKER
#VOLUMES = ['/opt/openjk/MBII','/opt/openjk/base','/opt/openjk/configs']

 
# Holds Global Variables / Configs
class globals:

    _VERBOSE = False
    _MB2_PATH = "/opt/openjk/MBII"
    _BASE_PATH = "/opt/openjk/base"
    _DOCKER_BASE_PATH = "/root/.local/share/openjk/MBII"
    _CONFIG_PATH = "/opt/openjk/configs"
    _VOLUME_BINDINGS =   {
                            '/opt/openjk/MBII': {'bind': '/opt/openjk/MBII', 'mode': 'rw'}, 
                            '/opt/openjk/base': {'bind': '/opt/openjk/base', 'mode': 'ro'}, 
                            '/opt/openjk/configs': {'bind': '/opt/openjk/configs', 'mode': 'ro'},              
                         }
 
# Random Tools and Helpers
class helpers:

    def fix_line(self, line):

      """Fix for the Client log line missing the \n (newline) character."""

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
    _DOCKER_INSTANCE_NAME = None 
    _DOCKER_INSTANCE = None
    
    _EXTERNAL_IP = None
    _PORT = None
    
    _SERVER_CONFIG_NAME = None
    _SERVER_CONFIG_PATH = None
    _RTVRTM_CONFIG_NAME = None
    _RTVRTM_CONFIG_PATH = None
    _SERVER_LOG_NAME = None
    _SERVER_LOG_PATH = None
    
    def __init__(self, name):
    
        self._NAME = name
        self._DOCKER_INSTANCE_NAME = "mbii-ded-" + name
        self._EXTERNAL_IP = urllib2.urlopen('http://ip.42.pl/raw').read()

        # server.CFG
        self._SERVER_CONFIG_NAME = self._NAME + "-server.cfg"
        self._SERVER_CONFIG_PATH = globals._CONFIG_PATH + "/" + self._SERVER_CONFIG_NAME
        
        # rtvrtm.CFG
        self._RTVRTM_CONFIG_NAME = self._NAME + "-rtvrtm.cfg"       
        self._RTVRTM_CONFIG_PATH = globals._CONFIG_PATH + "/" + self._RTVRTM_CONFIG_NAME    
        
        # games.log
        self._SERVER_LOG_NAME = self._NAME + "-games.log"
        self._SERVER_LOG_PATH = globals._DOCKER_BASE_PATH + "/" + self._SERVER_LOG_NAME
        
        self._DOCKER_INSTANCE = docker_instance(self._DOCKER_INSTANCE_NAME)
        
        # If instance running grab port
        if(self._DOCKER_INSTANCE.is_active()):
            self._PORT = self.get_port()
           
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

    # Will use this to get config info
    def server_config_info(self):
        return "*STILL NEED TO CODE THIS*"
       
    # Start an Interactive SSH Instance
    def ssh(self):   
        self._DOCKER_INSTANCE.ssh()
            
    # Get list of players in server        
    def players(self):
    
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
     
    # HH:MM:SS that MBIIDED has been running (not the docker)
    def uptime(self):

        if(self._DOCKER_INSTANCE.is_active()):
                    stream =  self._DOCKER_INSTANCE.exec_run('ps -eo pid,comm,lstart,etime,time,args') #FYI Using Bars to merely return a the number with GREP causing an error so doing parsing line by line here
                    for val in stream:
                        for item in val.split("\n"):
                            if("mbiided" in item):
                                return(item.split()[7])
                        
        return "00:00:00"
 
    # Current Map
    def map(self):

        stream = self._DOCKER_INSTANCE.read(self._SERVER_LOG_PATH)
        map = "unknown"

        for val in stream:

            for line in val.split("\n"):

                line = helpers().fix_line(line)
                line_comp = line.strip(",").split()
                try: 
                    if(line_comp[1] == "InitGame:"):                  
                        final_comp = line_comp      
                        
                except IndexError:
                    pass
                       

        try: 
            map = final_comp[7].split('\\')[30];
        except IndexError:
            pass

                       
        return map
     
    def start(self, port):

        self._PORT = port
        # Instance Running
        if(self._DOCKER_INSTANCE.is_active()):
            print(bcolors.OK + "Instance is already running..." + bcolors.ENDC)  
            return
            
        # Instance Needs Restart    
        if(self._DOCKER_INSTANCE.is_error()):
            print(bcolors.FAIL + "Instance Had Exited, Restarting..." + bcolors.ENDC)
            self._DOCKER_INSTANCE.stop()
        
        # Instance Can Start
        print("-------------------------------------------")
        print("Current MBII Version Is " + bcolors.OK + self._MB2_MANAGER.get_version() + bcolors.ENDC)
        print("-------------------------------------------")
        
        print("Docker Instance: " + self._DOCKER_INSTANCE_NAME)
        print("Port: " + self._PORT)
        print("IP Address: " + self._EXTERNAL_IP + ":" + self._PORT)       
        
        print("Server Log " + self._SERVER_LOG_PATH)
        print("-------------------------------------------")
         
        if(os.path.exists(self._SERVER_CONFIG_PATH)):
            print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Found SERVER config at " +  self._SERVER_CONFIG_PATH)
            
            if(os.path.exists(self._RTVRTM_CONFIG_PATH)):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Found RTVRTM config at " + self._RTVRTM_CONFIG_PATH + bcolors.ENDC)
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Enable Rock the Vote" + bcolors.ENDC)

            else:
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Found RTVRTM config at " +  self._RTVRTM_CONFIG_PATH + bcolors.ENDC)
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Enable Rock the Vote" + bcolors.ENDC)
                
            print("-------------------------------------------")
            self._DOCKER_INSTANCE.start(self._PORT, "MBII", self._SERVER_CONFIG_NAME, self._RTVRTM_CONFIG_NAME)

        else:
            print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Found SERVER config at " + self._SERVER_CONFIG_PATH)
            print(bcolors.FAIL + "Unable to proceed without a valid Server Config File" + bcolors.ENDC)
            exit()

    def status(self):

        self._PORT = self.get_port()

        print("-------------------------------------------")
        if(self._DOCKER_INSTANCE.is_active()):

            print(bcolors.CYAN + "Port: " + bcolors.ENDC + self._PORT)
            print(bcolors.CYAN + "Docker Instance: " + bcolors.ENDC + self._DOCKER_INSTANCE_NAME)
            print(bcolors.CYAN + "Server Name: " + bcolors.ENDC + self.server_config_info() )
            print(bcolors.CYAN + "Full Address: " + bcolors.ENDC + self._EXTERNAL_IP + ":" + self._PORT)
            print(bcolors.CYAN + "Map: " + bcolors.ENDC + self.map()) 
            print(bcolors.CYAN + "Uptime: " + bcolors.ENDC + self.uptime())
            print("-------------------------------------------")     
            print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Dedicated Server Running")
            
            if(self.get_rtv_status()):
                print(bcolors.OK + "[Yes] " + bcolors.ENDC + "RTV Service Running")            
            else:
                print(bcolors.FAIL + "[No] " + bcolors.ENDC + "RTV Service NOT Running")                       
          
            print("-------------------------------------------")   
                      
            print("Players ")
            
            players = self.players()
            
            for player_id in players:
                print(bcolors().mbii_color(players[player_id]))

        elif(self._DOCKER_INSTANCE.is_error()):
            print("     " + bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance in failed state" + bcolors.ENDC)
     
        elif(not self._DOCKER_INSTANCE.is_error() and not self._DOCKER_INSTANCE.is_active()):     
             print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Dedicated Server Running - Instance not started" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + self._DOCKER_INSTANCE_NAME + " is currently in " + self._DOCKER_INSTANCE.status() + " state" + bcolors.ENDC) 

        print("-------------------------------------------")

    def stop(self):
        self._DOCKER_INSTANCE.stop()

    def restart(self):     
        port = self._PORT
        self.stop()
        self.start(port)           
                        
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

class main:

    _INSTANCE_MANAGER = None
    _VERBOSE = False
    _PORT = None

    # Usage Banner
    def usage(self):
        print("usage:")
        print("MBII [-n -name] [-action {status start stop}] [-v -verbose]")  
        print("MBII [-n -name] -rcon <command>") 
        print("MBII [-n -name] -smod <command>")    
        print("MBII [-l -list]")

    # Main Function
    def main(self,argv):
    
        if(len(sys.argv) == 1):
            usage()
            exit()
            
        _INSTANCE_MANAGER = instance_manager()    
            
        parser = argparse.ArgumentParser()
        
        group = parser.add_mutually_exclusive_group()
        
        group.add_argument("-i", type=str, help="Action on Instance", nargs=2, metavar=('INSTANCE', 'ACTION'), dest="instance")   
        group.add_argument("-l", action="store_true", help="List Instances", dest="list")  
           
        group.add_argument("-u", action="store_true", help="Update MBII", dest="update")    
           
        parser.add_argument("-v", action="store_true", help="Verbosed Output", dest="verbose")   
        
        args = parser.parse_args()
        
        if(args.instance):
        
             getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])()
        
            #try:
                #getattr(_INSTANCE_MANAGER.get_instance(args.instance[0]), args.instance[1])()
                
            #except:
                #print("Invalid Command " + args.instance[1]) 
        
        elif(args.list): 
            _INSTANCE_MANAGER.list()

        elif(args.update):
            _INSTANCE_MANAGER.update()
        
        if(args.verbose):
            globals._VERBOSE = True

       
if __name__ == "__main__":
   main().main(sys.argv[1:])