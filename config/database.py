import os
import motor.motor_asyncio

class Database:
    def __init__(self):
        uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('MONGODB_DB_NAME', 'discord_bot')
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    # Collections
    @property
    def jobs(self): return self.db['jobs']
    
    @property
    def applications(self): return self.db['applications']
    
    @property
    def settings(self): return self.db['settings']
    
    @property
    def logs(self): return self.db['hr_logs']
    
    @property
    def staff_ranks(self): return self.db['staff_ranks']

    # Settings
    async def get_setting(self, key):
        doc = await self.settings.find_one({'_id': key})
        return doc['value'] if doc else None

    async def set_setting(self, key, value):
        await self.settings.update_one(
            {'_id': key}, {'$set': {'value': value}}, upsert=True
        )

    # HR Channel
    async def set_hr_channel(self, channel_id):
        await self.set_setting('hr_channel', channel_id)

    async def get_hr_channel(self):
        return await self.get_setting('hr_channel')

    # Log Channel
    async def set_log_channel(self, channel_id):
        await self.set_setting('log_channel', channel_id)

    async def get_log_channel(self):
        return await self.get_setting('log_channel')

    # Jobs
    async def add_job(self, name, description):
        await self.jobs.insert_one({
            'name': name,
            'description': description,
            'questions': []
        })

    async def get_all_jobs(self):
        return await self.jobs.find().to_list(None)

    async def get_job(self, name):
        return await self.jobs.find_one({'name': name})

    async def delete_job(self, name):
        await self.jobs.delete_one({'name': name})

    async def add_question(self, job_name, question):
        await self.jobs.update_one(
            {'name': job_name},
            {'$push': {'questions': question}}
        )

    async def remove_question(self, job_name, index):
        job = await self.get_job(job_name)
        if job and 0 <= index < len(job['questions']):
            del job['questions'][index]
            await self.jobs.update_one(
                {'name': job_name},
                {'$set': {'questions': job['questions']}}
            )
            return True
        return False

    # Applications
    async def add_application(self, user_id, user_name, job_name, answers):
        app = {
            'user_id': user_id,
            'user_name': user_name,
            'job_name': job_name,
            'answers': answers,
            'status': 'pending',
            'timestamp': __import__('datetime').datetime.utcnow()
        }
        result = await self.applications.insert_one(app)
        return result.inserted_id

    async def get_application(self, app_id):
        from bson import ObjectId
        return await self.applications.find_one({'_id': ObjectId(app_id)})

    async def update_application_status(self, app_id, status):
        from bson import ObjectId
        await self.applications.update_one(
            {'_id': ObjectId(app_id)},
            {'$set': {'status': status}}
        )

    async def get_all_applications(self, job_name=None):
        query = {'job_name': job_name} if job_name else {}
        return await self.applications.find(query).sort('timestamp', -1).to_list(None)

    # Logs
    async def add_log(self, app_id, reviewer_id, reviewer_name, decision, reason):
        await self.logs.insert_one({
            'application_id': app_id,
            'reviewer_id': reviewer_id,
            'reviewer_name': reviewer_name,
            'decision': decision,
            'reason': reason,
            'timestamp': __import__('datetime').datetime.utcnow()
        })

    async def get_all_logs(self, limit=50):
        return await self.logs.find().sort('timestamp', -1).limit(limit).to_list(None)

    async def get_reviewer_logs(self, reviewer_id):
        return await self.logs.find({'reviewer_id': reviewer_id}).sort('timestamp', -1).to_list(None)

    # Staff Ranks
    async def add_staff_rank(self, name, description, emoji, duties):
        await self.staff_ranks.insert_one({
            'name': name,
            'description': description,
            'emoji': emoji,
            'duties': duties
        })

    async def get_all_staff_ranks(self):
        return await self.staff_ranks.find().to_list(None)

    async def delete_staff_rank(self, name):
        await self.staff_ranks.delete_one({'name': name})


db = Database()
