import motor.motor_asyncio
import os

mongo_uri = os.environ.get("MONGO_URI", "mongodb://mongo_admin:password@localhost:27017/?authSource=admin")

client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = client.books