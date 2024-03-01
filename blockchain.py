import socket
import threading
import json
import hashlib
import time
import random

class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash, nonce):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash
        self.nonce = nonce

def calculate_hash(index, previous_hash, timestamp, data, nonce):
    block_string = str(index) + str(previous_hash) + str(timestamp) + json.dumps(data) + str(nonce)
    return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.lock = threading.Lock()

    def add_block(self, block):
        with self.lock:
            self.chain.append(block)

    def generate_block(self, data, previous_block):
        index = previous_block.index + 1
        timestamp = time.time()
        nonce = 0
        while True:
            hash_attempt = calculate_hash(index, previous_block.hash, timestamp, data, nonce)
            if hash_attempt.startswith("0000"):  # Adjust difficulty level as needed
                new_block = Block(index, previous_block.hash, timestamp, data, hash_attempt, nonce)
                self.add_block(new_block)
                return new_block
            else:
                nonce += 1

def handle_client(client_socket, blockchain, nodes):
    data = client_socket.recv(1024).decode()
    if data == "GET_CHAIN":
        response = json.dumps([vars(block) for block in blockchain.chain])
        client_socket.send(response.encode())
    elif data.startswith("ADD_NODE"):
        _, new_node = data.split(":")
        nodes.add(new_node)
        client_socket.send("Node added successfully.".encode())
    elif data.startswith("MINE_BLOCK"):
        _, miner_address = data.split(":")
        previous_block = blockchain.chain[-1]
        new_block_data = {
            "index": previous_block.index + 1,
            "previous_hash": previous_block.hash,
            "timestamp": time.time(),
            "data": "New Block",
        }
        mined_block = blockchain.generate_block(new_block_data, previous_block)
        broadcast_to_nodes(nodes, f"ADD_BLOCK:{json.dumps(vars(mined_block))}")
        client_socket.send("Block mined successfully.".encode())
    elif data.startswith("ADD_BLOCK"):
        _, block_data = data.split(":")
        block_data = json.loads(block_data)
        new_block = Block(**block_data)
        if validate_block(new_block, blockchain.chain[-1]):
            blockchain.add_block(new_block)
            client_socket.send("Block added successfully.".encode())
        else:
            client_socket.send("Invalid block.".encode())
    client_socket.close()

def validate_block(new_block, previous_block):
    # Basic validation: check index, previous hash, and hash
    if new_block.index != previous_block.index + 1:
        return False
    if new_block.previous_hash != previous_block.hash:
        return False
    if new_block.hash != calculate_hash(new_block.index, new_block.previous_hash, new_block.timestamp, new_block.data, new_block.nonce):
        return False
    return True

def start_server(blockchain, nodes, host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, blockchain, nodes))
        client_handler.start()

def send_request(host, port, request):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    client.send(request.encode())
    response = client.recv(1024).decode()
    client.close()
    return response

def broadcast_to_nodes(nodes, request):
    for node in nodes:
        host, port = node.split(":")
        response = send_request(host, int(port), request)
        print(f"Response from {node}: {response}")

if __name__ == "__main__":
    blockchain = Blockchain()
    nodes = set()  # Set to store the IP addresses and ports of connected nodes

    # Add a genesis block
    genesis_block = Block(0, "0", time.time(), "Genesis Block", "0000", 0)
    blockchain.add_block(genesis_block)

    # Start the server with your machine's IP address and a port number
    server_thread = threading.Thread(target=start_server, args=(blockchain, nodes, '0.0.0.0', 8888))
    server_thread.start()

    # Example: Connect to another node
    new_node_address = '192.168.1.2:8888'  # Replace with the actual address of another node
    response = send_request(new_node_address.split(":")[0], int(new_node_address.split(":")[1]), "ADD_NODE:" + "0.0.0.0:8888")
    print(response)

    # Example: Mine a new block
    miner_address = '0.0.0.0:8888'  # Replace with the actual address of the miner node
    response = send_request(miner_address.split(":")[0], int(miner_address.split(":")[1]), "MINE_BLOCK:" + miner_address)
    print(response)
