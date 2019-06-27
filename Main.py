from CControl.BlockChain.Structure import ClassControlBlockChain
from CControl.Utilities import Settings, get_network_ip, get_uuid, load_chain, push_peer
import threading
import time
import requests

#Point to one working node:
INITIAL_NODE_ADDRESS = "http://10.0.0.139:8693"
Settings(INITIAL_NODE_ADDRESS=INITIAL_NODE_ADDRESS)

#Initially we nee®d to load the blockchain that already exists out there by pointing it to an existing node:
data = load_chain(Settings().get("INITIAL_NODE_ADDRESS"))
first_server = False
if data == []: first_server = True
print(first_server)

blockchain = ClassControlBlockChain()
blockchain.load_initial_chain(data)
print(blockchain.chain)

from CControl.Backend.Main import Network

#Get local information
get_network_ip()
get_uuid()


#See if any identifying information is saved on the local computer
USERDATA = {}
try:
    with open('USERDATA.json') as json_file:
        USERDATA = json.load(json_file)
except(IOError):
    pass

#Now we can create our own node and initialize it with the current blockchain!
n = Network("CControl", blockchain)



def start_runner():
    ''' Adapted from: https://networklore.com/start-task-with-flask/
    Once Flask Server is Up and Running, we push peer to the nodes if this is not the first server
    '''
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:8693')
                print(r.status_code)
                if r.status_code == 404:
                    print('Server started, quiting start_loop')
                    if not first_server:
                        push_peer(**USERDATA)
                    not_started = False
                print(r.status_code)
            except:
                print('Server not yet started')
            time.sleep(2)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

if __name__ == "__main__":
    if not first_server: start_runner()
    n.run(host='0.0.0.0')