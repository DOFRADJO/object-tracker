from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["objet_tracker"]

objets_col = db["objets"]
frames_col = db["frames"]
