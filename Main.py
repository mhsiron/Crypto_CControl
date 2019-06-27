from CControl.BlockChain.Structure import ClassControlBlockChain
from CControl.Utilities import Settings, get_network_ip, get_uuid, load_chain, push_peer
import threading
import time

#Point to one working node:
INITIAL_NODE_ADDRESS = "http://10.0.0.139:8693"
Settings(INITIAL_NODE_ADDRESS=INITIAL_NODE_ADDRESS)

#Initially we need to load the blockchain that already exists out there by pointing it to an existing node:
data = load_chain(Settings().get("INITIAL_NODE_ADDRESS"))

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

print(1)

@n.before_first_request
def activate_job():
    def run_job():
        print("Registering node onto pointed server")
        # Now we need to tell the peer node we are connected to to add us to its node:
        push_peer(**USERDATA)
        time.sleep(3)

    thread = threading.Thread(target=run_job)
    thread.start()

# def start_runner():
#     def start_loop():
#         not_started = True
#         while not_started:
#             print('In start loop')
#             try:®
#                 r = requests.get('http://127.0.0.1:5000/')
#                 if r.status_code == 200:
#                     print('Server started, quiting start_loop')
#                     not_started = False
#                 print(r.status_code)
#             except:
#                 print('Server not yet started')
#             time.sleep(2)
#
#     print('Started runner')
#     thread = threading.Thread(target=start_loop)
#     thread.start()
#
# if __name__ == "__main__":
#     start_runner()
#     n.run()

#We then run our node and let it be accessible publicly!
n.run(host='0.0.0.0')

