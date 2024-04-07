from pymongo import MongoClient
def upload_users_to_mongodb(users_data):
        # Connect to MongoDB
        client = MongoClient('localhost', 27017)
        
        # Access the database
        db = client['drishti']
        
        # Access the collection (or create it if it doesn't exist)
        collection = db['users']
        
        # Insert the users data into the collection
        result = collection.insert_one(users_data)

users = {
    "users": {
        "volunteer": [
            None,
            {
                "current_ip": "http://100.97.225.126:8081",
                "location": {
                    "lat": 22.962601,
                    "lon": 76.046091
                }
            },
            {
                "current_ip": "http://100.97.225.126:8082",
                "location": {
                    "lat": 22.96317188502606,
                    "lon": 76.0449281707406
                }
            },
            {
                "current_ip": "http://100.97.225.126:8083",
                "location": {
                    "lat": 23.207129,
                    "lon": 75.582223
                }
            },
            {
                "current_ip": "http://100.97.225.126:8084",
                "location": {
                    "lat": 22.96260132,
                    "lon":  76.046091332
                }
            }
        ]
    }
}
def add_same_ip_location(users_data, current_ip, lat, lon):
    # Access the 'volunteer' list inside the 'users' object
    volunteer_list = users_data['users']['volunteer']
    
    # Find the index of the entry with the same current_ip, lat, and lon
    index = next((i for i, vol in enumerate(volunteer_list) if vol and vol['current_ip'] == current_ip
                  and vol['location']['lat'] == lat and vol['location']['lon'] == lon), None)
    
    if index is not None:
        # Insert a new entry with the same details after the found entry
        new_entry = {
            "current_ip": current_ip,
            "location": {
                "lat": lat,
                "lon": lon
            }
        }
        volunteer_list.insert(index + 1, new_entry)
        print("New entry with the same IP and location added successfully.")
    else:
        print("Entry with the provided IP and location not found.")

def get_all_users_from_mongodb():
    # Connect to MongoDB
    client = MongoClient('localhost', 27017)
    
    # Access the database
    db = client['drishti']
    
    # Access the collection
    collection = db['users']
    
    # Retrieve all documents from the collection
    all_users = collection.find()
    
    # Convert the cursor to a list of dictionaries
    users_list = list(all_users)
    
    return users_list

def find_similar_lat_lon(users_data):
    # Create a dictionary to store unique (lat, lon) pairs and their associated IPs
    lat_lon_to_ip = {}
    
      # Iterate through volunteer data
    for user_data in users_data:
        volunteer_list = user_data['users']['volunteer']
        for volunteer in volunteer_list:
            if volunteer:
                lat = volunteer['location']['lat']
                lon = volunteer['location']['lon']
                ip = volunteer['current_ip']
                # Check if the (lat, lon) pair already exists in the dictionary
                if (lat, lon) in lat_lon_to_ip:
                    # If it does, break from the loop as we've found the first occurrence
                    break
                else:
                    # Store the IP address for this (lat, lon) pair
                    lat_lon_to_ip[(lat, lon)] = ip
        else:
            # This will execute if the loop did not break, i.e., if the (lat, lon) pair was not found again
            continue
        # Break from outer loop if we found the first occurrence of the same (lat, lon) pair
        break
    
    return lat_lon_to_ip

allusers=get_all_users_from_mongodb()
similar_lat_lon_ips = find_similar_lat_lon(allusers)
print("Similar latitude and longitude coordinates with corresponding IPs:")
print(similar_lat_lon_ips)
    
    # Extract IP addresses from the matching doc

# Example usage:
# add_same_ip_location(users, "http://100.97.225.126:8080", 22.993933, 76.01195)

# upload the data to the database
# upload_users_to_mongodb(users)
# Print the updated users dictionary