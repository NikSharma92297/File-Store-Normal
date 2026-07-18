#Codeflix_Botz
#rohit_1888 on Tg

import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME
from bot import Bot
import logging
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)


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
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        


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


    # CHANNEL MANAGEMENT
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})
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

    # Method to clear all requests for a specific channel
    async def clear_channel_requests(self, channel_id: int):
        """
        Clears all user requests for a specific channel
        Returns the number of users removed
        """
        try:
            # Get the current document to count users
            channel_data = await self.rqst_fsub_Channel_data.find_one({'_id': int(channel_id)})
            user_count = len(channel_data.get('user_ids', [])) if channel_data else 0
            
            # Delete all user IDs for this channel by setting an empty array
            result = await self.rqst_fsub_Channel_data.update_one(
                {'_id': int(channel_id)},
                {'$set': {'user_ids': []}},
                upsert=True
            )
            
            return user_count
        except Exception as e:
            print(f"[DB ERROR] Failed to clear request list: {e}")
            return 0
    # Add these methods to the Rohit class in database/database.py

    # INVITE LINK MANAGEMENT
    
    async def invite_link_exist(self, channel_id: int):
        """Check if invite link exists for channel"""
        found = await self.database['invite_links'].find_one({'_id': channel_id})
        return bool(found)
    
    async def add_invite_link(self, channel_id: int):
        """Add channel to invite links with default settings"""
        if not await self.invite_link_exist(channel_id):
            await self.database['invite_links'].insert_one({
                '_id': channel_id,
                'mode': 'normal',  # 'normal' or 'request'
                'expiry': 0,  # 0 means no expiry, otherwise seconds
                'created_at': datetime.utcnow()
            })
    
    async def remove_invite_link(self, channel_id: int):
        """Remove invite link from database"""
        if await self.invite_link_exist(channel_id):
            await self.database['invite_links'].delete_one({'_id': channel_id})
    
    async def get_all_invite_links(self):
        """Get all channel IDs with invite links"""
        docs = await self.database['invite_links'].find().to_list(length=None)
        return [doc['_id'] for doc in docs]
    
    async def get_invite_settings(self, channel_id: int):
        """Get invite link settings for a channel"""
        data = await self.database['invite_links'].find_one({'_id': channel_id})
        if data:
            return {
                'mode': data.get('mode', 'normal'),
                'expiry': data.get('expiry', 0)
            }
        return {'mode': 'normal', 'expiry': 0}
    
    async def set_invite_mode(self, channel_id: int, mode: str):
        """Set invite link mode (normal or request)"""
        await self.database['invite_links'].update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )
    
    async def set_invite_expiry(self, channel_id: int, expiry: int):
        """Set invite link expiry time in seconds"""
        await self.database['invite_links'].update_one(
            {'_id': channel_id},
            {'$set': {'expiry': expiry}},
            upsert=True
        )
    # Add these methods to the Rohit class in database/database.py
# Place them after the set_invite_expiry method

    async def get_auto_approve(self, channel_id: int):
        """Get auto-approve setting for a channel"""
        data = await self.database['invite_links'].find_one({'_id': channel_id})
        if data:
            return data.get('auto_approve', False)
        return False
    
    async def set_auto_approve(self, channel_id: int, enabled: bool):
        """Set auto-approve for join requests"""
        await self.database['invite_links'].update_one(
            {'_id': channel_id},
            {'$set': {'auto_approve': enabled}},
            upsert=True
        )


db = Rohit(DB_URI, DB_NAME)
