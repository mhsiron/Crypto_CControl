from flask import Flask, request
import requests
import json
import sys
import time
from CControl.BlockChain.Structure import Command
from hashlib import sha256

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
            return "Block #{} is mined.".format(result)

        @self.app.route('/pending_tx')
        def get_pending_tx():
            return json.dumps({"pending_tx":[command for command in self.blockchain.unconfirmed_commands]})

        # endpoint to add new peers to the network.
        @self.app.route('/add_nodes', methods=['POST'])
        def register_new_peers():
            nodes = request.get_json(force=True)

            #Not required
            role_requested = nodes.get("role", False)
            otp = nodes.get("otp", False)
            root_access = nodes.get("grant", False)

            #Required
            node = nodes["node"]

            if not nodes:
                return "Invalid data", 400
            if self.peers.get(node, False) is False:
                otp = generate_one_time_password(node)

                if role_requested is False:
                    role_assigned = "STUDENT"

                self.peers[node] = {"otp":otp,"role":role_assigned}
                return json.dumps({"status":"REGISTERED","otp":otp, "role":role_assigned}).encode(), 201
            else:
                if not otp:
                    return json.dumps({"status":"NEED TO SUPPLY OTP"}).encode(), 678
                else:
                    print(self.peers.get(node)["otp"], file=sys.stderr)
                    print(otp, file=sys.stderr)
                    if self.peers.get(node)["otp"] == otp:
                        return json.dumps({"status":"LOGGED IN"}).encode(), 679
                    else:
                        return json.dumps({"status":"BAD PASSWORD"}).encode(), 680
            return json.dumps({"status":"Unknown"}).encode(), 200


        # endpoint to add a block mined by someone else to the node's chain.
        @self.app.route('/add_block', methods=['POST'])
        def validate_and_add_block():
            block_data = request.get_json()
            block = ClassControlBlock(block_data["index"], block_data["commands"],
                          block_data["timestamp", block_data["_previous_hash"]])
         
            proof = block_data['hash']
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
 
    for node in self.peers:
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
    timestamp = time.time()
    data = {"node":node_256, "timestamp":timestamp}
    all_data = json.dumps(data, sort_keys=True).encode()
    return sha256(all_data).hexdigest()


        