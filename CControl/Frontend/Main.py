#Set IP, PORTs
NETIP = "10.0.0.152" #Point to one working node
PORT = "8693"

#Set Possible Commands
COMMANDS_DICT = {
    "New Command":"/new_command",
    "Get Chains":"/chain",
    "Mined":"/mine",
    "Pending Transactions":"/pending_tx",
    "Add Node":"/add_nodes"
}


#Required imports
from uuid import getnode as get_mac
from hashlib import sha256
import socket
import requests
import json

#Get unique identifier for computer based on MAC address
MAC = get_mac()
UUID = sha256(str(MAC).encode()).hexdigest()
USERDATA = {}

#Get Local IP Address
HOSTNAME = socket.gethostname()
USERIP = socket.gethostbyname(HOSTNAME)
print(USERIP)



try:
    with open('USERDATA.json') as json_file:
        USERDATA = json.load(json_file)
except(IOError):
    pass

def push_peer(otp = False, role_requested = False, root_access = False, **kwargs):
	#URL to send commands to: 
    command_url = "http://"+NETIP+":"+PORT+COMMANDS_DICT["Add Node"]

    #Required parameters to pass
    data = {"node": str(UUID)}
    data["URL"] = USERIP

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



push_peer(**USERDATA)