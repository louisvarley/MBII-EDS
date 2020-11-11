#! bin/python
import sys, getopt
import os
import subprocess
import docker
import re
import urllib2

# Various Configs left here so they are accessable

#GLOBALS
NAME = None
MODE = None
PORT = None
ACTION = None
VERBOSE = False
INSTANCE_NAME = None

#DOCKER
VOLUMES = ['/opt/openjk/MBII','/opt/openjk/base','/opt/openjk/configs']
VOLUME_BINDINGS =   {
                    '/opt/openjk/MBII': {'bind': '/opt/openjk/MBII', 'mode': 'rw'}, 
                    '/opt/openjk/base': {'bind': '/opt/openjk/base', 'mode': 'ro'}, 
                    '/opt/openjk/configs': {'bind': '/opt/openjk/configs', 'mode': 'ro'},              
                    }
                             
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

# Docker Manager Class Handles everythings directly with the Docker.py Library
class docker_manager:

    # Probably could get these from Docker Library by NM
    _STATUS_RUNNING = "running"
    _STATUS_EXITED = "exited"
    _STATUS_NOT_FOUND = None
    
    # Will Hold the Docker Client Itself and Our Docker Instance Name
    _DOCKER = None
    _INSTANCE_NAME = None
    
    def __init__(self, Instance_Name):
        self._DOCKER = docker.from_env()
        self._INSTANCE_NAME = Instance_Name


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
    def start(self, port, game, server_config_name, rtvrtm_config_name, verbose = False):
        if(not self.is_active() and not self.is_error()):

                print(bcolors.OK + "Starting Instance of " + game + " on port " + port + "..." + bcolors.ENDC)

                container = self._DOCKER.containers.create(
                    image='bsencan/jedi-academy-server',
                    name=self._INSTANCE_NAME,
                    stdin_open=True,
                    tty=True,
                    command='/bin/sh',
                    volumes=VOLUME_BINDINGS,
                    network_mode ='host',
                    environment={"NET_PORT":port, "NET_GAME":game, "SERVER_CONFIG":server_config_name, "RTVRTM_CONFIG":rtvrtm_config_name}
                )    
                
                container.start()
                stream = container.exec_run("/opt/openjk/start.sh", stdout=verbose, stderr=verbose, stream=verbose)

                if(verbose):
                    for val in stream:
                        print (val)

class instance_manager:

    # Instance now, different from the Docker Instance name (more friendly version)
    _NAME = None
    
    # Docker Instance name 
    _DOCKER_INSTANCE_NAME = None
    
    # External IP   
    _EXTERNAL_IP = None
    
    # Port is set either when instance started or fetched if already running
    _PORT = None
    _DOCKER_MANAGER = None
    
    # If True, Continues to output Docker STDOUT once run
    _VERBOSE = False
    
    _SERVER_CONFIG_NAME = None
    _SERVER_CONFIG_PATH = None
    _RTVRTM_CONFIG_NAME = None
    _RTVRTM_CONFIG_PATH = None
    _SERVER_LOG_NAME = None
    _SERVER_LOG_PATH = None
    
    _CONFIG_PATH = "/opt/openjk/configs"
    _MB2_PATH = "/opt/openjk/MBII"
    _BASE_PATH = "/opt/openjk/base"
    
    _DOCKER_INSTANCE_NAME = None
    
    _MB2_MANAGER = None
    _OJK_MANAGER = None
    
    # Set Instance name and Get External IP
    def __init__(self, name, verbose):
        self._NAME = name
        self._DOCKER_INSTANCE_NAME = "openjk-ded-" + name
        self._EXTERNAL_IP = urllib2.urlopen('http://ip.42.pl/raw').read()
        self._VERBOSE = verbose
        
        self._MB2_MANAGER = mb2_manager(self._MB2_PATH)
        self._OJK_MANAGER = ojk_manager(self._BASE_PATH)
        # Work out the Locations of files
        
        # server.CFG
        self._SERVER_CONFIG_NAME = self._NAME + "-server.cfg"
        self._SERVER_CONFIG_PATH = self._CONFIG_PATH + "/" + self._SERVER_CONFIG_NAME
        
        # rtvrtm.CFG
        self._RTVRTM_CONFIG_NAME = self._NAME + "-rtvrtm.cfg"       
        self._RTVRTM_CONFIG_PATH = self._CONFIG_PATH + "/" + self._RTVRTM_CONFIG_NAME    
        
        # games.log
        self._SERVER_LOG_NAME = self._NAME + "-games.log"
        self._SERVER_LOG_PATH = self._MB2_PATH + "/" + self._SERVER_LOG_NAME
        
        self._DOCKER_MANAGER = docker_manager(self._DOCKER_INSTANCE_NAME)
        
        # If instance running grab port
        if(self._DOCKER_MANAGER.is_active()):
            self._PORT = self.get_port()
        
    # Method to Grab the Port used by OpenJK Server by running netstat
    def get_port(self):  
        port = 0
        if(self._DOCKER_MANAGER.is_active()):
            stream =  self._DOCKER_MANAGER.exec_run("netstat -tulpn | grep openjkded")
            for val in stream:
                for item in val.split("\n"):
                    if "openjkded" in item:
                        port = item.split()[3].split(":")[1];   

            if(port > 0):
                return str(port)  

        return None

    # Will use this to get config info
    def server_config_info(self):
        return "*STILL NEED TO CODE THIS*"
            
    # Start an instance, you must provide the port to use           
    def start(self, port):

        self._PORT = port
        # Instance Running
        if(self._DOCKER_MANAGER.is_active()):
            print(bcolors.OK + "Instance is already running..." + bcolors.ENDC)  
            return
            
        # Instance Needs Restart    
        if(self._DOCKER_MANAGER.is_error()):
            print(bcolors.FAIL + "Instance Had Exited, Restarting..." + bcolors.ENDC)
            self._DOCKER_MANAGER.stop()
        
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
            self._DOCKER_MANAGER.start(self._PORT, "MBII", self._SERVER_CONFIG_NAME, self._RTVRTM_CONFIG_NAME, self._VERBOSE)

        else:
            print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Found SERVER config at " + self._SERVER_CONFIG_PATH)
            print(bcolors.FAIL + "Unable to proceed without a valid Server Config File" + bcolors.ENDC)
            exit()

    def status(self):

        self._PORT = self.get_port()

        print("-------------------------------------------")
        if(self._DOCKER_MANAGER.is_active()):

            print("Port: " + self._PORT)
            print("Docker Instance: " + self._DOCKER_INSTANCE_NAME)
            print("Server Name " + self.server_config_info() )
            print("Full Address " + self._EXTERNAL_IP + ":" + self._PORT)
            print("-------------------------------------------")     
            print(bcolors.OK + "[Yes] " + bcolors.ENDC + "Running")

        elif(self._DOCKER_MANAGER.is_error()):
            print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Running - Instance in failed state" + bcolors.ENDC)
     
        elif(not self._DOCKER_MANAGER.is_error() and not self._DOCKER_MANAGER.is_active()):     
             print(bcolors.FAIL + "[No] " + bcolors.ENDC + "Running - Instance not started" + bcolors.ENDC)
        else:
            print(bcolors.FAIL + self._DOCKER_INSTANCE_NAME + " is currently in " + self._DOCKER_MANAGER.status() + " state" + bcolors.ENDC) 

        print("-------------------------------------------")

    def stop(self):
        self._DOCKER_MANAGER.stop()

    def restart(self, name):     
        port = self._PORT
        self.stop()
        self.start(port)


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
            
        opts, argv = getopt.getopt(sys.argv[1:], 'n:a:p:v')   
     
        VERBOSE=False
        PORT=None
     
        for opt, arg in opts:
   
            # Manage Instance Name
            if(opt == "-n" or opt == "-name"):
                NAME=arg
                MODE="MANAGE"
                
             # Set Port
            if(opt == "-p" or opt == "-port"):
                PORT=arg          
                
            # Enable Vebose
            if(opt == "-v" or opt == "-v"):
                VERBOSE=True
                
            # Manage Action    
            if(opt == "-a" or opt == "-action"):
                ACTION=arg.upper()

            # List All Configs
            if(opt == "-l" or opt == "-list"):
                MODE="LIST"
        
            # Help
            if opt == '-h':
                usage()
                sys.exit()
          
        # Missing Instance Name for Manage Mode
        if(MODE == "MANAGE"):
            if(NAME == None):
                 print(bcolors.FAIL + "You Must Include an Instance Name to Manage an Instance" + bcolors.ENDC)  
                 exit()
        
        # Start an Instance of Instance Manager        
        _INSTANCE_MANAGER = instance_manager(NAME, VERBOSE)
            
        # START Action 
        if(ACTION == "START"):
                
            # Missing PORT for Start Action    
            if(PORT == None):
                print(bcolors.FAIL + "You Must Include a PORT to Start an Instance" + bcolors.ENDC)
                exit()
        
            _INSTANCE_MANAGER.start(PORT)
                
        if(ACTION == "STATUS" and  NAME != None):
            _INSTANCE_MANAGER.status()
                
        if(ACTION == "STOP" and  NAME != None):
            _INSTANCE_MANAGER.stop() 

        if(ACTION == "RESTART" and  NAME != None):
            _INSTANCE_MANAGER.restart()            
       
if __name__ == "__main__":
   main().main(sys.argv[1:])