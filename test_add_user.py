import requests

url = "http://127.0.0.1:5000/add_user"

data = {
    "user_info": {
        "full_name": "Madhav Beri",
        "age": 20,
        "email": "madhav@example.com",
        "phone": "9876543210"
    },
    "contacts": [
        {
            "name": "Sonakshi",
            "relation": "Friend",
            "email": "sonakshi@example.com",
            "phone": "9999999999"
        },
        {
            "name": "Muskan",
            "relation": "Sister",
            "email": "muskan@example.com",
            "phone": "8888888888"
        }
    ]
}

response = requests.post(url, json=data)
print(response.json())
