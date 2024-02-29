from hashlib import sha256, md5
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO
from PIL import Image
import io

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(proof=100)

    def new_block(self, proof):
        # Create a new block and add it to the chain
        previous_hash = '1' if not self.chain else self.hash(self.chain[-1])
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }

        # Reset the current transactions list
        self.current_transactions = []

        # Append the block to the chain
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, image):
        # Create a new transaction and add it to the current transactions list
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'image': image,
        })

    def hash(self, block):
        # Hash a block using SHA-256
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        # Proof of work algorithm (example)
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, last_proof, proof):
        # Example: Check if the hash of the concatenated proofs contains leading zeros
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def mine(self, sender):
        # Mine a new block
        last_block = self.chain[-1]
        last_proof = last_block['proof']
        proof = self.proof_of_work(last_proof)

        # Create a new transaction (miner's reward)
        recipient = sender  # Miner's own address for reward
        self.new_transaction(sender, recipient, "miner_reward_image")

        # Create the new block
        new_block = self.new_block(proof)
        return new_block

    def get_chain(self):
        # Return the full chain
        response = {
            'chain': self.chain,
            'length': len(self.chain),
        }
        return jsonify(response), 200



app = Flask(__name__)
socketio = SocketIO(app)
blockchain = Blockchain()


@socketio.on('connect')
def handle_connect():
    global blockchain
    blockchain.nodes.add(request.sid)
    print(f"Node {request.sid} connected.")
    socketio.emit('update_chain', {'chain': blockchain.chain}, room=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    global blockchain
    blockchain.nodes.remove(request.sid)
    print(f"Node {request.sid} disconnected.")


@socketio.on('new_transaction')
def handle_new_transaction(data):
    global blockchain
    image = request.files['image'].read()
    blockchain.new_transaction(data['sender'], data['recipient'], image)
    broadcast_chain()

@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/mine', methods=['POST'])
def mine():
    global blockchain
    try:
        # Extract sender address from the request 
        sender = request.form.get('sender')

        # Validate that the sender is present
        if not sender:
            return jsonify({'error': 'Sender address is missing'}), 400

        # Mine a new block
        mined_block = blockchain.mine(sender)
        broadcast_chain()

        response = {
            'message': "New block mined",
            'index': mined_block['index'],
            'transactions': mined_block['transactions'],
            'proof': mined_block['proof'],
            'previous_hash': mined_block['previous_hash'],
        }

        socketio.emit('mine_response', response, namespace='/', room=request.sid) 
        return jsonify(response), 200
    except ValueError as e:
        response = {'error': str(e)}
        socketio.emit('mine_response', response, namespace='/', room=request.sid) 
        return jsonify(response), 400
    except Exception as e:
        response = {'error': f'Internal Server Error: {str(e)}'}
        return jsonify(response), 500


@socketio.on('update_chain')
def handle_update_chain(data):
    global blockchain
    new_chain = data['chain']
    if len(new_chain) > len(blockchain.chain) and valid_chain(new_chain):
        blockchain.chain = new_chain
        print("Chain updated.")
        broadcast_chain()


def valid_chain(chain):
    last_block = chain[0]
    current_index = 1

    while current_index < len(chain):
        block = chain[current_index]
        if block['previous_hash'] != blockchain.hash(last_block):
            return False
        if not blockchain.valid_proof(last_block['proof'], block['proof']):
            return False
        last_block = block
        current_index += 1

    return True


def broadcast_chain():
    global blockchain
    socketio.emit('update_chain', {'chain': blockchain.chain}, broadcast=True)


def valid_chain(chain):
    last_block = chain[0]
    current_index = 1

    while current_index < len(chain):
        block = chain[current_index]
        if block['previous_hash'] != blockchain.hash(last_block):
            return False
        if not blockchain.valid_proof(last_block['proof'], block['proof']):
            return False
        last_block = block
        current_index += 1

    return True


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
