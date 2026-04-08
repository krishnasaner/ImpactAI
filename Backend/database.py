from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from config import MONGO_URI, MONGO_DB_NAME

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[MONGO_DB_NAME]
users_collection = db["users"]
chat_collection = db["chat_sessions"]


def init_indexes() -> None:
    users_collection.create_index("email", unique=True)
    chat_collection.create_index("session_id")
    chat_collection.create_index("created_at")


class DuplicateEmailError(DuplicateKeyError):
    pass
