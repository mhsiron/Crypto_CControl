from flask import Flask, request
import requests
import json
import time
from hashlib import sha256
import sys
from CControl.BlockChain.Structure import ClassControlBlock

class Network:
    def __init__(self, name, blockchain, port = 8693):
        self.app =  Flask(name)
        self.name = name
        self.blockchain = blockchain

        # the address to other participating members of the network
        self.peers = dict()

        

        # This allows us to create a POST request to submit a new command !
        @self.app.route('/new_command', methods=['POST'])
        def new_command():
            cmd_data = request.get_json()
            required_fields = ["source", "module","command_parameters","destination"]
         
            for field in required_fields:
                if not cmd_data.get(field):
                    return "Invalid Command Input", 404
            #cmd_data["timestamp"] = time.time()
            self.blockchain.add_new_command(**cmd_data)
            return "Success", 201

        #Used to query all the blocks in the chain!
        @self.app.route('/chain', methods=['GET'])
        def get_chain():
            chain_data = []
            for block in self.blockchain.chain:
                chain_data.append(block.__dict__)
            return json.dumps({"length": len(chain_data),
                               "chain": chain_data})
        #request the mining!
        @self.app.route('/mine', methods=['GET'])
        def mine_unconfirmed_commands():
            result = self.blockchain.mine()
            if not result:
                return "No transactions to mine"
            announce_new_block(self.blockchain.chain[-1])
            return "Block #{} is mined.".format(result)

        @self.app.route('/pending_cmd')
        def get_pending_cmd():
            return json.dumps({"pending_tx":[command for command in self.blockchain.unconfirmed_commands]})

        # endpoint to add new peers to the network.
        @self.app.route('/add_nodes', methods=['POST'])
        def register_new_peers():
            nodes = request.get_json(force=True)

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

                self.peers[node] = {"otp":otp,"role":role_assigned,"URL":url}
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
            block_data = request.get_json(force = True)
            print(block_data, file=sys.stderr)
            block = ClassControlBlock(block_data["index"], block_data["commands"],
                          block_data["timestamp"], block_data["_previous_hash"])
         
            proof = block_data['_hash']
            added = self.blockchain.add_block(block, proof)
         
            if not added:
                return "The block was discarded by the node", 400
         
            return "Block added to the chain", 201

        def announce_new_block(block):
            for peer in self.peers:
                url = "http://{}/add_block".format(peer)
                requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))

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