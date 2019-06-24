from CControl.BlockChain.Structure import ClassControlBlock
from CControl.BlockChain.Structure import ClassControlBlockChain
from CControl.BlockChain.Structure import Endpoint

from flask import Flask, request, render_template
import requests
import json

blockchain = ClassControlBlockChain()

from CControl.Backend.Main import Network

n = Network("CCControl", blockchain)

import datetime
import json
 
import requests
from flask import render_template, redirect, request

import sys

import ast
 
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8693"
 
posts = []

def fetch_posts():
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for cmd in block["commands"]:
                if type(cmd) == type("str"):
                    cmd = ast.literal_eval(cmd)
                cmd["index"] = block["index"]
                cmd["hash"] = block["_previous_hash"]
                cmd["timestamp"] = block["timestamp"]
                content.append(cmd)
 
        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)

@n.app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    source = request.form["source"]
    module = request.form["module"]
    command_parameters = request.form["command_parameters"]
    destination = request.form["destination"]
 
    post_object = {
        'source': source,
        'module': module,
        'command_parameters' :command_parameters,
        'destination' :destination
    }
 
    # Submit a transaction
    new_cmd_address = "{}/new_command".format(CONNECTED_NODE_ADDRESS)
 
    requests.post(new_cmd_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})
 
    return redirect('/')

@n.app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                           title='CControl: Admin Portal',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)
def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')

n.run(host='0.0.0.0')