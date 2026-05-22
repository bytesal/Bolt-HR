import os
import motor.motor_asyncio

class Database:
    def __init__(self):
        uri = os.getenv('MONGODB_URI')
        print(f"🔍 MONGODB_URI = {uri}")  # ← سطر تشخيصي
        db_name = os.getenv('MONGODB_DB_NAME', 'discord_bot')
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
    # ... باقي الكود كما هو
