# db.py
from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["object_tracking_db"]
tracking_collection = db["tracking_data"]


def save_tracking_data(video_id, tracking_data):
    document = {
        "video_id": video_id,
        "data": tracking_data
    }
    result = tracking_collection.insert_one(document)
    return str(result.inserted_id)


def get_tracking_data(video_id):
    document = tracking_collection.find_one({"video_id": video_id})
    if document:
        document["_id"] = str(document["_id"])
        return document
    return None
