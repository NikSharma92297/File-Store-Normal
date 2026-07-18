# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, ChannelPrivate, PeerIdInvalid, ChatAdminRequired
from bot import Bot
from config import *
from helper_func import *
from database.database import *

BAN_SUPPORT = f"{BAN_SUPPORT}"

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is banned
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    m = await message.reply_text("♻️")
    await asyncio.sleep(0.5)
    await m.edit_text("<code>Checking.</code>")
    await asyncio.sleep(0.4)
    await m.edit_text("<code>Checking..</code>")
    await asyncio.sleep(0.4)
    await m.edit_text("<code>Checking...</code>")
    await asyncio.sleep(0.6)
    await m.delete()

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Handle command arguments
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return

        string = await decode(base64_string)
        
        # ==================== HANDLE INVITE LINKS ====================
        if string.startswith("inv_"):
            try:
                # Extract channel ID from string like "inv_-1001234567890"
                ch_id_str = string.replace("inv_", "")
                ch_id = int(ch_id_str)
            except (ValueError, IndexError) as e:
                print(f"Error parsing invite link: {e}, string: {string}")
                return await message.reply_text(
                    "<b>❌ Invalid link format!</b>\n\n"
                    "<i>Contact @IntrovertSama for support.</i>"
                )
    
            # Check if link exists in database
            if not await db.invite_link_exist(ch_id):
                return await message.reply_text(
                    "<b>🚫 This link has been revoked by admins!</b>\n\n"
                    "<i>Contact @IntrovertSama for more information.</i>"
                )
    
            try:
                # Get channel info
                chat = await client.get_chat(ch_id)
                
                # Get settings
                settings = await db.get_invite_settings(ch_id)
                mode = settings['mode']
                expiry = settings['expiry']
                
                # Get auto-delete timer
                FILE_AUTO_DELETE = await db.get_del_timer()
                
                # Generate invite link based on mode and expiry
                try:
                    if mode == "request":
                        # Create join request link
                        invite = await client.create_chat_invite_link(
                            chat_id=ch_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=expiry) if expiry > 0 else None
                        )
                    else:
                        # Create normal invite link
                        invite = await client.create_chat_invite_link(
                            chat_id=ch_id,
                            expire_date=datetime.utcnow() + timedelta(seconds=expiry) if expiry > 0 else None
                        )
                    
                    invite_link = invite.invite_link
                    
                    # Determine expiry text
                    if expiry > 0:
                        expiry_text = get_exp_time(expiry)
                        expiry_msg = f"\n<b>⏳ Link expires in:</b> {expiry_text}"
                    else:
                        expiry_msg = ""
                    
                    # Send invite link to user
                    invite_msg = await message.reply_text(
                        f"<b>🎉 Here's your invite link!</b>\n\n"
                        f"<b>Channel:</b> {chat.title}\n"
                        f"<b>Type:</b> {'🟢 Join Request' if mode == 'request' else '🔵 Direct Invite'}"
                        f"{expiry_msg}\n\n"
                        f"<b>🔗 Invite Link:</b>\n<code>{invite_link}</code>\n\n"
                        f"<i>Click the button below to join!</i>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📢 Join Channel", url=invite_link)]
                        ]),
                        disable_web_page_preview=True
                    )
                    
                    # Auto-delete the invite link message if enabled
                    if FILE_AUTO_DELETE > 0:
                        notification_msg = await message.reply(
                            f"<b>Tʜɪs Iɴᴠɪᴛᴇ Lɪɴᴋ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(FILE_AUTO_DELETE)}. ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>"
                        )
                        
                        await asyncio.sleep(FILE_AUTO_DELETE)
                        
                        # Delete the invite message
                        try:
                            await invite_msg.delete()
                        except Exception as e:
                            print(f"Error deleting invite message: {e}")
                        
                        # Generate new link for "Get Link Again" button
                        enc_id = await encode(f"inv_{ch_id}")
                        reload_url = f"https://t.me/{client.username}?start={enc_id}"
                        
                        keyboard = InlineKeyboardMarkup(
                            [[InlineKeyboardButton("ɢᴇᴛ ʟɪɴᴋ ᴀɢᴀɪɴ!", url=reload_url)]]
                        )
                        
                        try:
                            await notification_msg.edit(
                                "<b>ʏᴏᴜʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ɪs sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ 👇</b>",
                                reply_markup=keyboard
                            )
                        except Exception as e:
                            print(f"Error updating notification with 'Get Link Again' button: {e}")
                    
                    return
                    
                except ChatAdminRequired:
                    await message.reply_text(
                        "<b>❌ Bot is not an admin in this channel!</b>\n\n"
                        "<i>Contact @IntrovertSama to fix this issue.</i>"
                    )
                    return
                    
                except Exception as e:
                    print(f"Error creating invite link: {e}")
                    await message.reply_text(
                        f"<b>❌ Failed to generate invite link!</b>\n\n"
                        f"<b>Error:</b> <code>{str(e)}</code>\n\n"
                        f"<i>Contact @IntrovertSama for support.</i>"
                    )
                    return
                    
            except ChannelPrivate:
                await message.reply_text(
                    "<b>❌ Bot is not a member of this channel!</b>\n\n"
                    "<i>Contact @IntrovertSama to fix this issue.</i>"
                )
                return
                
            except PeerIdInvalid:
                await message.reply_text(
                    "<b>❌ Invalid channel!</b>\n\n"
                    "<i>This link may have been broken. Contact @IntrovertSama</i>"
                )
                return
                
            except Exception as e:
                print(f"Error in invite link handler: {e}")
                await message.reply_text(
                    f"<b>❌ An error occurred!</b>\n\n"
                    f"<b>Error:</b> <code>{str(e)}</code>\n\n"
                    f"<i>Contact @IntrovertSama for support.</i>"
                )
                return
        
        # ==================== HANDLE FILE LINKS (EXISTING CODE) ====================
        # Check Force Subscription
        if not await is_subscribed(client, user_id):
            return await not_joined(client, message)

        # File auto-delete time
        FILE_AUTO_DELETE = await db.get_del_timer()

        # Continue with existing file handling logic
        argument = string.split("-")

        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return

        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
                return

        temp_msg = await message.reply("<b>Please wait...</b>")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
        finally:
            await temp_msg.delete()

        codeflix_msgs = []
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, 
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                codeflix_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass

        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"<b>Tʜɪs Fɪʟᴇ ᴡɪʟʟ ʙᴇ Dᴇʟᴇᴛᴇᴅ ɪɴ  {get_exp_time(FILE_AUTO_DELETE)}. Pʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs Dᴇʟᴇᴛᴇᴅ.</b>"
            )

            await asyncio.sleep(FILE_AUTO_DELETE)

            for snt_msg in codeflix_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")

            try:
                reload_url = (
                    f"https://t.me/{client.username}?start={message.command[1]}"
                    if message.command and len(message.command) > 1
                    else None
                )
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]
                ) if reload_url else None

                await notification_msg.edit(
                    "<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Error updating notification with 'Get File Again' button: {e}")
    else:
        # No arguments - show welcome message
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/as_networks")],
                [
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data = "about"),
                    InlineKeyboardButton('ʜᴇʟᴘ •', callback_data = "help")
                ]
            ]
        )
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586)  # 🔥
        
        return



#=====================================================================================##
# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport



# Create a global dictionary to store chat data
chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<b><i>ᴡᴀɪᴛ ᴀ sᴇᴄ..</i></b>")

    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()  # Should return list of (chat_id, mode) tuples
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)  # fetch mode 

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    # Cache chat info
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    # Simplified check - just use the username as indicator for public/private
                    is_public = bool(data.username)
                    
                    # Generate appropriate invite link
                    try:
                        if not is_public and mode == "on":
                            # Private channel with join request mode
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                creates_join_request=True,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                        else:
                            # Public channel or private channel without join request
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                        link = invite.invite_link
                    except Exception as e:
                        print(f"Failed to create invite link: {e}")
                        # Fallback to username link only if generating invite link fails
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            raise  # Re-raise the exception if no fallback available

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b>{'! ' * count}</b>")

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @rohit_1888</i></b>\n"
                        f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
                    )

        # Retry Button
        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")
        await temp.edit(
            f"<b><i>! Eʀʀᴏʀ, Cᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ sᴏʟᴠᴇ ᴛʜᴇ ɪssᴜᴇs @rohit_1888</i></b>\n"
            f"<blockquote expandable><b>Rᴇᴀsᴏɴ:</b> {e}</blockquote>"
        )
        await temp.delete
#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data = "close")]])
    await message.reply(text=CMD_TXT, reply_markup = reply_markup, quote= True)
