import time
from hashlib import sha256
import json
import sys
class ClassControlBlock:
    ''' A class control block can contain multiple commands.
    Traditionally, a block should contain all related commands 
    (ie if you send multiple receivers the same exact command).
    This is useful for organizing blocks. But in reality it is
    controlled by when the blocks are mined.
    A block should not contain any data - all data should be in commands!'''
    def __init__(self, index, commands, timestamp, previous_hash, nonce=0):
        self._hash = None
        self.index = index
        self.commands = commands 
        self.timestamp = timestamp
        self._previous_hash = previous_hash
        self._hash = self.compute_hash()
        self.nonce = nonce
    def compute_hash(self):
        '''
        Turns the current block into a hash, by converting the object's dictionary to a string
        and passing it through the sha256 library. When we run this function it is important to 
        remove the _hash keyword itself from the string
        '''
        block_string = dict(self.__dict__)
        block_string.pop("_hash")
        block_string = json.dumps(block_string, sort_keys=True)
        print(block_string, file=sys.stderr)
        return sha256(block_string.encode()).hexdigest()

class ClassControlBlockChain:
    difficulty = 2 #sets how difficult algorithm is.
    problem = 'a'
    #In future versions, only "TEACHERS" and "ADMINISTRATORS" will be able to create a block
    '''
    The objects that holds all the blocks together and performs the PoW algorithm to add a block onto it.
    '''
 
    def __init__(self):
        '''
        Initialize a block with default value, and by creating the genesis block
        '''
        self.unconfirmed_commands = [] # commands yet to get into blockchain
        self.chain = []
        self.__create_genesis_block() #hidden command, should not be accessible
        self._first = True
 
    def __create_genesis_block(self):
        """
        Creates the first block in the chain with index 0!
        """
        if len(self.chain) is not 0:
            raise TypeError('Genesis Block already exists. Nice try!')
        else:
            genesis_block = ClassControlBlock(0, [], time.time(), "0")
            self.chain.append(genesis_block)
    def load_initial_chain(self, json_data):
        '''
        We use this to load an existing chain from the network!
        If we don't find what we need in the data, the chain remains not updated..
        :param json_data:
        :return:
        '''
        if isinstance(json_data ,dict):
            if not json_data.get("chain", False):
                print("not valid format...")
            else:
                temp_chain = json_data.get("chain")
                self.chain = []
                self._first = False
                for chain in temp_chain:
                    n = ClassControlBlock(index = chain["index"],commands = chain["commands"],
                                          timestamp = chain["timestamp"],
                                          previous_hash=chain["_previous_hash"])
                    n._hash = chain["_hash"]
                    self.chain.append(n)

        else:
            print("Not valid existing blockchain... Check network")

    def proof_of_work(self, block):
        """
        Proof of work works by solving a problem. Here we have a simple problem because for our 
        purpose we want to avoid long computations. In fact for this application, we don't really need a PoW algorithm.
        Either way - the problem is that the first 'difficulty' characters have to be 'problem' in the hash. So a new hash
        is elevatuated until that is the case.
        """
        block.nonce = 0
 
        computed_hash = block.compute_hash()
        #the PoW problem to solve is to make sure that the computed hash has the first two bytes being:
        b = ClassControlBlockChain.problem
        while not computed_hash.startswith(b * ClassControlBlockChain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
 
        return computed_hash
    def add_block(self, block, proof):
        """
        Once the PoW is satisfied, the block is added to the chain.
        """
        print("Add Block on BCX ran", file=sys.stderr)
        _previous_hash = self.last_block._hash
 
        if _previous_hash != block._previous_hash:
            return False
 
        if not self.is_valid_proof(block, proof):
            return False
 
        block._hash = proof
        print(proof, file=sys.stderr)
        print(block.compute_hash(), file=sys.stderr)
        self.chain.append(block)
        self.unconfirmed_commands = []
        return True
 
    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        print("Is valid proof ran", file=sys.stderr)
        print(block, file=sys.stderr)
        print(hash, file=sys.stderr)
        #the PoW problem to solve is to make sure that the computed hash has the first two bytes being:
        b = ClassControlBlockChain.problem
        print((block_hash.startswith(b * ClassControlBlockChain.difficulty)), file=sys.stderr)
        print(block_hash == block.compute_hash(), file=sys.stderr)
        print(block.compute_hash(), file=sys.stderr)
        print(block_hash, file=sys.stderr)
        return (block_hash.startswith(b * ClassControlBlockChain.difficulty) and
                block_hash == block.compute_hash())
    
    def add_new_command(self, **kwargs):
        '''
        Adds a command to be later mined. In theory, when all related commands have been added, self.mine() 
        should be executed
        '''
        self.unconfirmed_commands.append(Command(**kwargs).to_json())
 
    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof of Work.
        """
        if not self.unconfirmed_commands:
            return False
 
        last_block = self.last_block
 
        new_block = ClassControlBlock(index=last_block.index + 1,
                          commands=self.unconfirmed_commands,
                          timestamp=time.time(),
                          previous_hash=last_block._hash)
 
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        return new_block.index
    
    @property
    def last_block(self):
        return self.chain[-1]
class Command:
    ''' Helper class to format commands properly '''
    # A command must be formatted the following way:
    # {
    #     "source": "some_author_name", #hash of authoring
    #     "module": "modName", #this is which file it will invoke on the host computer
    #     "command_parameters":{"command_param_1":"param_1"} #what to pass onto the module
    #     "destination": "some destination", #hash of receiver
    #     "status":"BROADCAST",
    # }
    def __init__(self, source, module, command_parameters, destination):
        self.source = source
        self.module = module
        self.command_parameters = command_parameters
        self.destination = destination
        self.status = "BROADCAST"
    def update_status(self, new_status):
        self.status = new_status
    def to_json(self):
        return json.dumps(self.__dict__, sort_keys=True)

class Endpoint:
    def __init__(self, username, role, room):
        self._uuid = None
        self.username = username
        self.role = role
        self.room = room
        self._time_created = time.time()
        self._uuid = self.compute_hash()
    def compute_hash(self):
        '''
        Turns the current block into a hash, by converting the object's dictionary to a string
        and passing it through the sha256 library. When we run this function it is important to 
        remove the _hash keyword itself from the string
        '''
        endpoint_string = dict(self.__dict__)
        endpoint_string.pop("_uuid")
        endpoint_string = str(endpoint_string).encode("utf-8")
        return sha256(endpoint_string).hexdigest()