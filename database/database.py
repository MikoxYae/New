#Yaemiko_Botz
#rohit_1888 on Tg

import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME, PROTECT_CONTENT, CUSTOM_CAPTION
import logging
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)

def new_user(id):
    return {
        '_id': id,
    }

class Rohit:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users']
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.bot_settings_data = self.database['bot_settings']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        self.maintenance_data = self.database['maintenance']
        self.media_buttons_data = self.database['media_buttons']
        


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

    # SUPPORT LINK (for Support button shown to users in receipts / errors)
    async def set_support_link(self, value):
        await self.bot_settings_data.update_one(
            {'_id': 'support_link'},
            {'$set': {'value': value}},
            upsert=True
        )

    async def get_support_link(self):
        data = await self.bot_settings_data.find_one({'_id': 'support_link'})
        if data is None:
            return None
        return data.get('value')

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

    # FREE LINK ON/OFF TOGGLE
    # ON  -> daily limit is enforced; after limit user must buy premium
    # OFF -> no limit at all; everyone can fetch content freely
    async def get_free_link_enabled(self):
        doc = await self.bot_settings_data.find_one({'_id': 'free_link_enabled'})
        return bool(doc.get('value', True)) if doc else True

    async def set_free_link_enabled(self, enabled: bool):
        await self.bot_settings_data.update_one(
            {'_id': 'free_link_enabled'},
            {'$set': {'value': bool(enabled)}},
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


    # ──────────────────────────────────────────────────────────────────
    # MEDIA BUTTONS
    # ──────────────────────────────────────────────────────────────────
    # Inline buttons (1 button per row) attached to every file/media that
    # the bot delivers via /start <encoded_link> — this covers /genlink,
    # /batch and /custom_batch links because they all flow through the
    # same delivery path in plugins/start.py.
    #
    # Stored as a single document with an ordered `buttons` array:
    #   { _id: 'media_buttons', buttons: [ {name: 'Join', url: 'https://t.me/x'}, ... ] }
    # Indexes are 0-based and match the array position.

    async def get_media_buttons(self) -> list:
        """Return the ordered list of media buttons. Empty list if none."""
        doc = await self.media_buttons_data.find_one({'_id': 'media_buttons'})
        if not doc:
            return []
        return list(doc.get('buttons', []) or [])

    async def add_media_button(self, name: str, url: str) -> int:
        """Append a new button. Returns the new total count."""
        buttons = await self.get_media_buttons()
        buttons.append({'name': str(name), 'url': str(url)})
        await self.media_buttons_data.update_one(
            {'_id': 'media_buttons'},
            {'$set': {'buttons': buttons}},
            upsert=True
        )
        return len(buttons)

    async def remove_media_button(self, index: int) -> bool:
        """Remove the button at the given 0-based index. Returns True on success."""
        buttons = await self.get_media_buttons()
        if index < 0 or index >= len(buttons):
            return False
        buttons.pop(index)
        await self.media_buttons_data.update_one(
            {'_id': 'media_buttons'},
            {'$set': {'buttons': buttons}},
            upsert=True
        )
        return True

    async def edit_media_button(self, index: int, name: str = None, url: str = None) -> bool:
        """Update name and/or url for the button at the given index."""
        buttons = await self.get_media_buttons()
        if index < 0 or index >= len(buttons):
            return False
        if name is not None:
            buttons[index]['name'] = str(name)
        if url is not None:
            buttons[index]['url'] = str(url)
        await self.media_buttons_data.update_one(
            {'_id': 'media_buttons'},
            {'$set': {'buttons': buttons}},
            upsert=True
        )
        return True


db = Rohit(DB_URI, DB_NAME)
