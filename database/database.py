#Yaemiko_Botz
#rohit_1888 on Tg

import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME, PROTECT_CONTENT, CUSTOM_CAPTION, ANTI_BYPASS_ENABLED
import logging
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

class Rohit:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users']
        self.sex_data = self.database['sex']
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.bot_settings_data = self.database['bot_settings']
        self.verify_attempts_data = self.database['verify_attempts']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        self.shortner_settings_data = self.database['shortner_settings']
        self.maintenance_data = self.database['maintenance']
        


    # USER DATA
    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        await self.user_data.insert_one({'_id': user_id})
        return

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return


    # ADMIN DATA
    async def admin_exist(self, admin_id: int):
        found = await self.admins_data.find_one({'_id': admin_id})
        return bool(found)

    async def add_admin(self, admin_id: int):
        if not await self.admin_exist(admin_id):
            await self.admins_data.insert_one({'_id': admin_id})
            return

    async def del_admin(self, admin_id: int):
        if await self.admin_exist(admin_id):
            await self.admins_data.delete_one({'_id': admin_id})
            return

    async def get_all_admins(self):
        users_docs = await self.admins_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids


    # BAN USER DATA
    async def ban_user_exist(self, user_id: int):
        found = await self.banned_user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({'_id': user_id})
            return

    async def del_ban_user(self, user_id: int):
        if await self.ban_user_exist(user_id):
            await self.banned_user_data.delete_one({'_id': user_id})
            return

    async def get_ban_users(self):
        users_docs = await self.banned_user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids



    # AUTO DELETE TIMER SETTINGS
    async def set_del_timer(self, value: int):        
        existing = await self.del_timer_data.find_one({})
        if existing:
            await self.del_timer_data.update_one({}, {'$set': {'value': value}})
        else:
            await self.del_timer_data.insert_one({'value': value})

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        if data:
            return data.get('value', 600)
        return 0


    # BOT SETTINGS
    async def set_protect_content(self, value: bool):
        await self.bot_settings_data.update_one(
            {'_id': 'protect_content'},
            {'$set': {'value': bool(value)}},
            upsert=True
        )

    async def get_protect_content(self):
        data = await self.bot_settings_data.find_one({'_id': 'protect_content'})
        if data is None:
            return PROTECT_CONTENT
        return bool(data.get('value', PROTECT_CONTENT))

    async def set_custom_caption(self, value):
        await self.bot_settings_data.update_one(
            {'_id': 'custom_caption'},
            {'$set': {'value': value}},
            upsert=True
        )

    async def get_custom_caption(self):
        data = await self.bot_settings_data.find_one({'_id': 'custom_caption'})
        if data is None:
            return CUSTOM_CAPTION
        return data.get('value')

    async def set_anti_bypass(self, value: bool):
        await self.bot_settings_data.update_one(
            {'_id': 'anti_bypass'},
            {'$set': {'value': bool(value)}},
            upsert=True
        )

    async def get_anti_bypass(self):
        data = await self.bot_settings_data.find_one({'_id': 'anti_bypass'})
        if data is None:
            return ANTI_BYPASS_ENABLED
        return bool(data.get('value', ANTI_BYPASS_ENABLED))


    # CHANNEL MANAGEMENT
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id, 'mode': 'off', 'request_link': ''})
            return

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})
            return

    async def show_channels(self):
        channel_docs = await self.fsub_data.find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids

    
# Get current mode of a channel
    async def get_channel_mode(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    # Set mode of a channel
    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    async def get_request_link(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("request_link", "") if data else ""

    async def set_request_link(self, channel_id: int, link: str):
        await self.fsub_data.update_one(
            {'_id': channel_id},
            {'$set': {'request_link': link}},
            upsert=True
        )

    # REQUEST FORCE-SUB MANAGEMENT

    # Add the user to the set of users for a   specific channel
    async def req_user(self, channel_id: int, user_id: int):
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'_id': int(channel_id)},
                {'$addToSet': {'user_ids': int(user_id)}},
                upsert=True
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to add user to request list: {e}")


    # Method 2: Remove a user from the channel set
    async def del_req_user(self, channel_id: int, user_id: int):
        # Remove the user from the set of users for the channel
        await self.rqst_fsub_Channel_data.update_one(
            {'_id': channel_id}, 
            {'$pull': {'user_ids': user_id}}
        )

    # Check if the user exists in the set of the channel's users
    async def req_user_exist(self, channel_id: int, user_id: int):
        try:
            found = await self.rqst_fsub_Channel_data.find_one({
                '_id': int(channel_id),
                'user_ids': int(user_id)
            })
            return bool(found)
        except Exception as e:
            print(f"[DB ERROR] Failed to check request list: {e}")
            return False  


    # Method to check if a channel exists using show_channels
    async def reqChannel_exist(self, channel_id: int):
    # Get the list of all channel IDs from the database
        channel_ids = await self.show_channels()
        #print(f"All channel IDs in the database: {channel_ids}")

    # Check if the given channel_id is in the list of channel IDs
        if channel_id in channel_ids:
            #print(f"Channel {channel_id} found in the database.")
            return True
        else:
            #print(f"Channel {channel_id} NOT found in the database.")
            return False



    # VERIFICATION MANAGEMENT
    async def db_verify_status(self, user_id):
        user = await self.user_data.find_one({'_id': user_id})
        if user:
            return user.get('verify_status', default_verify)
        return default_verify

    async def db_update_verify_status(self, user_id, verify):
        await self.user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

    async def get_verify_status(self, user_id):
        verify = await self.db_verify_status(user_id)
        return verify

    async def update_verify_status(self, user_id, verify_token="", is_verified=False, verified_time=0, link="", created_at=None, risk_score=0, risk_reasons=None):
        current = await self.db_verify_status(user_id)
        current['verify_token'] = verify_token
        current['is_verified'] = is_verified
        current['verified_time'] = verified_time
        current['link'] = link
        if created_at is not None:
            current['created_at'] = created_at
        if risk_reasons is not None:
            current['risk_score'] = risk_score
            current['risk_reasons'] = risk_reasons
        await self.db_update_verify_status(user_id, current)

    async def mark_verify_passed(self, user_id, token, ip="", user_agent="", risk_score=0, risk_reasons=None):
        current = await self.db_verify_status(user_id)
        if current.get('verify_token') != token:
            return False
        current['is_verified'] = True
        current['verified_time'] = time.time()
        current['verified_ip'] = ip
        current['verified_user_agent'] = user_agent
        current['risk_score'] = risk_score
        current['risk_reasons'] = risk_reasons or []
        await self.db_update_verify_status(user_id, current)
        return True

    async def log_verify_attempt(self, user_id, token, ip="", user_agent="", passed=False, risk_score=0, risk_reasons=None):
        now = time.time()
        await self.verify_attempts_data.insert_one({
            'user_id': int(user_id),
            'token': token,
            'ip': ip,
            'user_agent': user_agent[:300] if user_agent else "",
            'passed': bool(passed),
            'risk_score': int(risk_score),
            'risk_reasons': risk_reasons or [],
            'created_at': now
        })
        await self.verify_attempts_data.delete_many({'created_at': {'$lt': now - 86400}})

    async def count_recent_verify_attempts(self, ip="", user_agent="", seconds=600):
        since = time.time() - seconds
        ip_count = 0
        ua_count = 0
        if ip:
            ip_count = await self.verify_attempts_data.count_documents({'ip': ip, 'created_at': {'$gte': since}})
        if user_agent:
            ua_count = await self.verify_attempts_data.count_documents({'user_agent': user_agent[:300], 'created_at': {'$gte': since}})
        return ip_count, ua_count

    # Set verify count (overwrite with new value)
    async def set_verify_count(self, user_id: int, count: int):
        await self.sex_data.update_one({'_id': user_id}, {'$set': {'verify_count': count}}, upsert=True)

    # Get verify count (default to 0 if not found)
    async def get_verify_count(self, user_id: int):
        user = await self.sex_data.find_one({'_id': user_id})
        if user:
            return user.get('verify_count', 0)
        return 0

    # Reset all users' verify counts to 0
    async def reset_all_verify_counts(self):
        await self.sex_data.update_many(
            {},
            {'$set': {'verify_count': 0}} 
        )

    # Get total verify count across all users
    async def get_total_verify_count(self):
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$verify_count"}}}
        ]
        result = await self.sex_data.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0


    # MAINTENANCE MODE
    async def get_maintenance(self):
        doc = await self.maintenance_data.find_one({'_id': 'maintenance'})
        return doc.get('enabled', False) if doc else False

    async def set_maintenance(self, enabled: bool):
        await self.maintenance_data.update_one(
            {'_id': 'maintenance'},
            {'$set': {'enabled': enabled}},
            upsert=True
        )

    # SHORTNER ENABLED / DISABLED TOGGLE
    async def get_shortner_enabled(self):
        doc = await self.bot_settings_data.find_one({'_id': 'shortner_enabled'})
        return bool(doc.get('value', True)) if doc else True

    async def set_shortner_enabled(self, value: bool):
        await self.bot_settings_data.update_one(
            {'_id': 'shortner_enabled'},
            {'$set': {'value': bool(value)}},
            upsert=True
        )

    # FREE LINK DAILY LIMIT
    async def get_free_link_limit(self):
        doc = await self.bot_settings_data.find_one({'_id': 'free_link_limit'})
        return int(doc.get('value', 5)) if doc else 5

    async def set_free_link_limit(self, value: int):
        await self.bot_settings_data.update_one(
            {'_id': 'free_link_limit'},
            {'$set': {'value': int(value)}},
            upsert=True
        )

    # USER DAILY LINK COUNT
    async def get_user_daily_links(self, user_id: int):
        today = datetime.now().strftime('%Y-%m-%d')
        doc = await self.user_data.find_one({'_id': user_id})
        if not doc:
            return 0
        daily = doc.get('daily_links', {})
        if daily.get('date') != today:
            return 0
        return int(daily.get('count', 0))

    async def increment_user_daily_links(self, user_id: int):
        today = datetime.now().strftime('%Y-%m-%d')
        doc = await self.user_data.find_one({'_id': user_id})
        if not doc:
            return
        daily = doc.get('daily_links', {})
        if daily.get('date') != today:
            new_daily = {'date': today, 'count': 1}
        else:
            new_daily = {'date': today, 'count': int(daily.get('count', 0)) + 1}
        await self.user_data.update_one({'_id': user_id}, {'$set': {'daily_links': new_daily}})

    # SHORTNER SETTINGS
    async def get_shortner_settings(self):
        doc = await self.shortner_settings_data.find_one({'_id': 'shortner'})
        if doc:
            return doc
        return {}

    async def save_shortner_settings(self, draft: dict):
        try:
            expire = int(draft.get('expire', 60))
        except (ValueError, TypeError):
            expire = 60
        await self.shortner_settings_data.update_one(
            {'_id': 'shortner'},
            {'$set': {
                'url':     draft.get('url', ''),
                'api':     draft.get('api', ''),
                'expire':  expire,
                'tut_vid': draft.get('tut_vid', ''),
            }},
            upsert=True
        )


db = Rohit(DB_URI, DB_NAME)
