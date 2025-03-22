from pymongo.mongo_client import MongoClient # type: ignore

uri = "mongodb+srv://admin1:cn242@cluster0.fum1o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri)
db = client["user_database"]
users_collection = db["users"]

try:
    client.admin.command("ping")
    print("Connected to MongoDB successfully!")
except Exception as e:
    print("MongoDB connection error:", e)
