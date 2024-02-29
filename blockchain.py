
from flask import Flask, jsonify, request
import requests
import json
import hashlib
import time

class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash, proof):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash
        self.proof = proof

class Blockchain:
    def __init__(self):
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.add_block(previous_hash='1', proof=100)

    def add_block(self, previous_hash, proof):
        index = len(self.chain) + 1
        timestamp = time.time()
        data = f"Block {index} data"
        hash = self.calculate_hash(index, previous_hash, timestamp, data, proof)
        block = Block(index, previous_hash, timestamp, data, hash, proof)
        self.chain.append(block)
        return block

    def calculate_hash(self, index, previous_hash, timestamp, data, proof):
        value = f"{index}{previous_hash}{timestamp}{data}{proof}"
        return hashlib.sha256(value.encode()).hexdigest()

    def proof_of_work(self, previous_proof):
        proof = 0
        while not self.valid_proof(previous_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(previous_proof, proof):
        guess = f"{previous_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Instantiate the blockchain
blockchain = Blockchain()

# Instantiate the Flask app
app = Flask(__name__)

@app.route('/mine', methods=['GET'])
def mine():
    # Proof of Work
    previous_block = blockchain.chain[-1]
    previous_proof = previous_block.proof
    proof = blockchain.proof_of_work(previous_proof)

    # Add the new block to the blockchain
    previous_hash = blockchain.calculate_hash(
        previous_block.index,
        previous_block.previous_hash,
        previous_block.timestamp,
        previous_block.data,
        previous_block.proof
    )
    block = blockchain.add_block(previous_hash, proof)

    response = {
        'message': 'New block mined!',
        'index': block.index,
        'hash': block.hash,
        'proof': block.proof,
        'data': block.data,
        'timestamp': block.timestamp
    }
    return jsonify(response), 200

# Create an RPC endpoint to get the full blockchain
@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': [block.__dict__ for block in blockchain.chain],
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# RPC server endpoint to register new nodes
@app.route('/register_node', methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        blockchain.nodes.add(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

# RPC server endpoint to reach consensus between nodes
@app.route('/resolve', methods=['GET'])
def consensus():
    neighbors = blockchain.nodes
    new_chain = None

    # Find the longest chain among all nodes
    max_length = len(blockchain.chain)

    for node in neighbors:
        response = requests.get(f'http://{node}/chain')
        if response.status_code == 200:
            length = response.json()['length']
            chain = response.json()['chain']

            if length > max_length and blockchain.is_valid_chain(chain):
                max_length = length
                new_chain = chain

    if new_chain:
        blockchain.chain = [Block(**block) for block in new_chain]
        response = {
            'message': 'Chain updated',
            'new_chain': [block.__dict__ for block in blockchain.chain],
        }
    else:
        response = {
            'message': 'Chain unchanged',
            'chain': [block.__dict__ for block in blockchain.chain],
        }

    return jsonify(response), 200

# Run the Flask app
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
