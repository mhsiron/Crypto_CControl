from CControl.BlockChain.Structure import ClassControlBlockChain
from CControl.Utilities import Settings, get_network_ip, get_uuid, load_chain, push_peer
import json

#Point to one working node:
INITIAL_NODE_ADDRESS = "http://10.0.0.139:8693"
Settings(INITIAL_NODE_ADDRESS=INITIAL_NODE_ADDRESS)

#Initially we nee®d to load the blockchain that already exists out there by pointing it to an existing node:
data = load_chain(Settings().get("INITIAL_NODE_ADDRESS"))
first_server = False
if data == []: first_server = True

blockchain = ClassControlBlockChain()
blockchain.load_initial_chain(data)
print([chain.__dict__ for chain in blockchain.chain])

from CControl.Backend.Main import Network

#Get local information
get_network_ip()
get_uuid()

print(Settings().__dict__)


#See if any identifying information is saved on the local computer
USERDATA = {}
try:
    with open('USERDATA.json') as json_file:
        USERDATA = json.load(json_file)
except(IOError):
    pass

#Now we can create our own node and initialize it with the current blockchain!
n = Network("CControl", blockchain)

if not first_server:
    push_peer(**USERDATA)
    #n.peers.append()

n.run(host='0.0.0.0')