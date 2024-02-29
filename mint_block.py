import requests
import sys

node_address = "http://localhost:5000"
sender_address = "ben"  # Replace with the actual sender address

# Ensure an image file path is provided as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python mint_block.py <image_file_path>")
    sys.exit(1)

image_path = sys.argv[1]

# Read the image file
with open(image_path, "rb") as image_file:
    image_data = image_file.read()

# Prepare the multipart/form-data request
files = {'image': ('image_file', image_data, 'image/jpeg')}
data = {'sender': sender_address}

# Send the POST request to mine a new block
response = requests.post(f"{node_address}/mine", files=files, data=data)

# Print the response
print(response.json())

# Print the raw response content
print("Raw Response Content:")
print(response.content)

# Try to decode the JSON response
try:
    json_response = response.json()
    print("Decoded JSON Response:")
    print(json_response)
except requests.exceptions.JSONDecodeError as e:
    print("JSON Decode Error:", e)
