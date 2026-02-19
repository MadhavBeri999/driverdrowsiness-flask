import requests

# URL of your local backend
url = "http://localhost:5000/add_user"

# JSON data your backend expects
data = {
    "user_info": {
        "full_name": "John Doe",
        "age": 30,
        "email": "john@example.com",
        "phone": "1234567890"
    },
    "contacts": [
        {
            "name": "Jane Doe",
            "relation": "Wife",
            "email": "jane@example.com",
            "phone": "9876543210"
        }
    ]
}

# Make the POST request
response = requests.post(url, json=data)

# Print the response from the server
print("Status Code:", response.status_code)
print("Response Body:", response.text)
