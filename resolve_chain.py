import requests

# Replace with the actual IP address and port of the machine running the Flask app
FLASK_APP_URL = 'http://localhost:5000'

def resolve_nodes():
    url = f'{FLASK_APP_URL}/nodes/resolve'

    response = requests.get(url)

    if response.status_code == 200:
        print("Consensus achieved. Blockchain resolved successfully.")
        print(response.text)  
    else:
        print(f"Failed to resolve nodes. Status code: {response.status_code}")

if __name__ == "__main__":
    resolve_nodes()