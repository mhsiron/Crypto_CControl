import requests
import socket
from uuid import getnode as get_mac
from hashlib import sha256
import json

class AllData:
    data = {}

class Settings(AllData):
    def __init__(self, **kwargs):
        self.data.update(kwargs)
        self.__dict__ = self.data
    def get(self, key):
        return self.data.get(key, False)

#Set Possible Commands
COMMANDS_DICT = {
    "New Command":"/new_command",
    "Get Chains":"/chain",
    "Mined":"/mine",
    "Pending Transactions":"/pending_tx",
    "Add Node":"/add_nodes"
}

def load_chain(origin_server):
    try:
        get_chain_address = "{}/chain".format(origin_server)
        response = requests.get(get_chain_address)
        return response.json()
    except:
        print("Refused")
        return []

def push_peer(otp = False, role_requested = False, root_access = False, **kwargs):
    USERDATA = {}
	#URL to send commands to:
    s = Settings()
    command_url = s.get("INITIAL_NODE_ADDRESS")+COMMANDS_DICT["Add Node"]
    print(command_url)

    #Required parameters to pass
    data = {"node": s.get("UUID")}
    data["URL"] = s.get("USERIP")

    #Optional paramteters to pass
    if role_requested: data["role_requested"] = role_requested
    if otp: data["otp"] = otp
    if root_access: data["root_access"]=root_access

    #send POST requests and get response:
    r1 = requests.post(command_url, data=json.dumps(data).encode())
    r1_response = r1.json()

    #Analyze response:
    if r1.status_code == 201:
        print("New User! Please save your OTP somewhere. By default, will create data file")
        USERDATA["otp"] = r1_response["otp"]
        USERDATA["role"] = r1_response["role"]

        with open('USERDATA.json', 'w') as outfile:
            json.dump(USERDATA, outfile)

    elif r1.status_code == 678:
        print("Peer already exist but you didn't supply correct password")
    elif r1.status_code == 679:
        print("Peer already exist. You supplied correct password!")
    else:
        print("Unknown error :(")
    return r1_response["status"]

def get_network_ip():
    # Get Local IP Address
    HOSTNAME = socket.gethostname()
    USERIP = socket.gethostbyname(HOSTNAME)
    Settings(USERIP=USERIP)
    return USERIP

def get_uuid():
    # Get unique identifier for computer based on MAC address
    MAC = get_mac()
    UUID = sha256(str(MAC).encode()).hexdigest()
    Settings(UUID=UUID)
    return UUID