from flask import Flask, request
import requests
import json
import time
from hashlib import sha256
import sys
from CControl.BlockChain.Structure import Command, ClassControlBlock
from CControl.Utilities import Settings

class Network:
    def __init__(self, name, blockchain, s, port = 8693):
        self.app =  Flask(name)
        self.name = name
        self.blockchain = blockchain

        # the address to other participating members of the network
        self.peers = dict()

        #Get our peer
        self.node = s.get("UUID")

        #Get our role
        self.role_assigned = "STUDENT"
        if self.blockchain._first:
            self.role_assigned = "TEACHER"

        #Get our otp
        self.otp = s.get("otp")
        if not self.otp:
            self.otp = generate_one_time_password(self.node)

        self.url = s.get("URL")

        self.me = {"node":self.node,"otp":self.otp,"role":self.role_assigned,"URL":self.url,"status":"ONLINE","URL_otp_hosted":s.get("USERIP")}
        print(self.me)
        my_peer = dict(self.me)
        my_peer.pop("node")
        self.peers[self.me["node"]] = my_peer
        print(self.peers.keys())

        # This allows us to create a POST request to submit a new command !
        @self.app.route('/new_command', methods=['POST'])
        def new_command():
            print("New Command Ran", file=sys.stderr)
            cmd_data = request.get_json()
            print(cmd_data, file=sys.stderr)
            required_fields = ["source", "module","command_parameters","destination","node","otp"]
         
            for field in required_fields:
                if not cmd_data.get(field):
                    return "Invalid Command Input", 404
            #cmd_data["timestamp"] = time.time()
            input_data = dict(cmd_data)
            input_data.pop("node")
            input_data.pop("otp")

            if cmd_data["node"] not in self.peers.keys():
                return "You must register peer first", 300
            elif validate_otp(node = cmd_data["node"], otp=cmd_data["otp"])[1] != 900:
                #Only authenticated people can add blocks...
                return "Bad OTP", 301
            elif "TEACHER" not in validate_otp(node = cmd_data["node"], otp=cmd_data["otp"])[0]:
                #Only people with role as "TEACHER" can add blocks...
                return "Role not allowed to send command...", 302
            else:
                self.blockchain.add_new_command(**input_data)
                return "Success", 200

        #Used to query all the blocks in the chain!
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            print("Get Chain Ran", file=sys.stderr)
            chain_data = []
            for block in self.blockchain.chain:
                chain_data.append(block.__dict__)
            return json.dumps({"length": len(chain_data),
                               "chain": chain_data})
        #request the mining!
        @self.app.route('/mine', methods=['GET'])
        def mine_unconfirmed_commands():
            print("Mine_Unconfirmed_Commands ran", file=sys.stderr)
            result = self.blockchain.mine()
            if not result:
                return "No transactions to mine"
            announce_new_block(self.blockchain.chain[-1])
            return "Block #{} is mined.".format(result)

        @self.app.route('/pending_cmd')
        def get_pending_cmd():
            print("Get pending cmd ran", file=sys.stderr)
            return json.dumps({"pending_tx":[command for command in self.blockchain.unconfirmed_commands]})

        # endpoint to add new peers to the network.
        @self.app.route('/add_nodes', methods=['POST'])
        def register_new_peers():
            print("Register new peer ran", file=sys.stderr)
            nodes = request.get_json(force=True)
            print(nodes, file=sys.stderr)

            #Not required parameters
            role_requested = nodes.get("role", False)
            otp = nodes.get("otp", False)
            root_access = nodes.get("grant", False)

            #Required information
            node = nodes["node"]
            url = None
            if not nodes.get("URL", False):
                return False
            else:
                url = nodes["URL"]

            if not nodes or url is None or node is None:
                #Checks to make sure valid data was inputted
                return "Invalid data", 400
            elif self.peers.get(node, False) is False:
                #No node exists, generate a new node and send them their one time password (OTP)
                otp = generate_one_time_password(node)

                #Checks what role the person requested
                if role_requested is False or role_requested == "STUDENT":
                    role_assigned = "STUDENT"

                if len(self.peers) >0 and (role_requested is not False or role_requested is not "STUDENT"):
                    # this is where we will have to determine whether or not we should grant a specific role to user upon request. TO DO!
                    # for now we won't allow this.
                    role_assigned = "STUDENT"


                self.peers[node] = {"otp":otp,"role":role_assigned,"URL":url,"status":"ONLINE","URL_otp_hosted":Settings().get("USERIP")}
                return json.dumps({"status":"REGISTERED","otp":otp, "role":role_assigned}).encode(), 201
            else:
                #Valid data is inputted AND node already exists
                if not otp:
                    #If this runs, the user did not input their password but the node already exists. Error code 678.
                    return json.dumps({"status":"NEED TO SUPPLY OTP"}).encode(), 678
                else:
                    #If this runs, the user inputted their password
                    #Check if correct password was submmited
                    if self.peers.get(node)["otp"] == otp:

                        #update URL if new IP Address is detected for logged in PC
                        if self.peers.get(node)["URL"] != url:
                            self.peers.get(node)["URL"] = url

                        #update status if status is OFFLINE:
                        if self.peers.get(node)["status"] == "OFFLINE":
                            self.peers.get(node)["status"] == "ONLINE"

                        #Status 679 means logged in, correct password!
                        return json.dumps({"status":"LOGGED IN"}).encode(), 679
                    else:
                        #If this runs, the user inputted a bad password.
                        return json.dumps({"status":"BAD PASSWORD"}).encode(), 680

            #If this is returned I'm not sure what happened, so 200 means an unknown error - no logic was run
            return json.dumps({"status":"Unknown"}).encode(), 200


        # endpoint to add a block mined by someone else to the node's chain.
        @self.app.route('/add_block', methods=['POST'])
        def validate_and_add_block():
            print("Validate and add block ran", file=sys.stderr)
            block_data = request.get_json(force = True)
            print(block_data, file=sys.stderr)
            print(type(block_data["commands"]), file=sys.stderr)
            commands = []
            for element in block_data["commands"]:
                element = json.loads(element)
                commands.append(Command(element["source"], element["module"],
                                        element["command_parameters"],element["destination"]).to_json())

            block = ClassControlBlock(block_data["index"], commands,
                          block_data["timestamp"], block_data["_previous_hash"], nonce = block_data["nonce"])
         
            proof = block_data['_hash']
            added = self.blockchain.add_block(block, proof)
         
            if not added:
                return "The block was discarded by the node", 400
         
            return "Block added to the chain", 201

        def announce_new_block(block):
            print("Announce new block ran", file=sys.stderr)
            for node, peer in self.peers.items():
                print(peer, file=sys.stderr)
                if peer["status"] == "ONLINE" and node != self.me["node"]:
                    print("Online", file=sys.stderr)
                    try:
                        url = "http://{}/add_block".format(peer["URL"])
                        print(url, file=sys.stderr)
                        print(block.__dict__, file=sys.stderr)
                        r1 = requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))
                        print(r1.status_code)
                        print("tried success", file=sys.stderr)
                    except:
                        #If an error happens, the node is probably offline:
                        self.peers[node]["status"] = "OFFLINE"

        @self.app.route('/validate_otp', methods=["POST"])
        def validate_otp(node = None, otp=None):
            '''
            This will be the method that validates otp wherever otp is located...
            '''
            print("Validate OTP ran", file=sys.stderr)
            validate_data = request.get_json()


            if node == None and otp == None:
                node = validate_data.get("node", False)
                otp = validate_data.get("otp", False)

            if not node or not otp:
                return "Invalid Data", 901
            print(self.peers)
            if not self.peers.get(node, False):
                return "peer cannot be found..."
            elif not self.peers.get(node).get("otp", False):
                url = "http://{}:8693/validate_otp".format(self.peers.get(node).get("URL_otp_hosted"))
                r1 = requests.post(url, data=json.dumps({"ndde":node,"otp":otp}, sort_keys=True))
                return r1.data
            elif self.peers.get(node).get("otp") == otp:
                return json.dumps({"result":True, "role":self.peers.get(node).get("role")}), 900
            else:
                return json.dumps({"result":False}), 902


    def run(self, port=8693, host=None):
        self.app.run(debug=True, port=port, host=host)

def consensus():
    """
    Our simple consensus algorithm. If a longer valid chain is found, our chain is replaced with it.
    """
    global blockchain
 
    longest_chain = None
    current_len = len(blockchain)
 
    for node_info in self.peers:
        node = node_info["URL"]
        response = requests.get('http://{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and self.blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain
 
    if longest_chain:
        blockchain = longest_chain
        return True
 
    return False
def generate_one_time_password(node_256):
    '''
    This function is used to generate one time passwords for new peers.
    It is a hash generation based on both the node hash and the timestamp in which the node was registered.
    '''
    timestamp = time.time()
    data = {"node":node_256, "timestamp":timestamp}
    all_data = json.dumps(data, sort_keys=True).encode()
    return sha256(all_data).hexdigest()