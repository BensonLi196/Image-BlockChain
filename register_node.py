import requests

# Replace with the actual IP address and port of the machine running the Flask app
FLASK_APP_URL = 'http://10.0.0.220:5000'

def register_node(node_url):
    url = f'{FLASK_APP_URL}/nodes/register'
    data = {'nodes': node_url}

    response = requests.post(url, json=data)

    if response.status_code == 201:
        print(f"Node {node_url} registered successfully.")
    else:
        print(f"Failed to register node {node_url}. Status code: {response.status_code}")
        print(response.text)  # Print the response content
        
if __name__ == "__main__":
    # Replace <other_node_ip> and <other_node_port> with the IP address and port of the node you want to register
    other_node_url = '10.0.0.220:5000'
    
    register_node(other_node_url)