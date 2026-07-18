# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport

import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import ChatAdminRequired, PeerIdInvalid, ChannelPrivate
from bot import Bot
from config import OWNER_ID
from helper_func import encode, decode, admin
from database.database import db
from pyrogram.errors import UserNotParticipant

# ==================== ADD INVITE LINK ====================
@Bot.on_message(filters.command('add_invite') & filters.private & admin)
async def add_invite_link(client: Client, message: Message):
    """
    Command: /add_invite <channel_id>
    Creates an invite link for a channel and returns encoded bot link
    """
    temp = await message.reply("<b><i>Processing...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)
    
    if len(args) != 2:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>Format:</b> <code>/add_invite -100XXXXXXXXXX</code>\n"
            "<b>Example:</b> <code>/add_invite -1001234567890</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        )
    
    try:
        ch_id = int(args[1])
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID format!</b>")
    
    # Check if already exists
    if await db.invite_link_exist(ch_id):
        # Get existing settings
        settings = await db.get_invite_settings(ch_id)
        mode = "🟢 Request" if settings['mode'] == "request" else "🔵 Normal"
        expiry = f"{settings['expiry']}s" if settings['expiry'] > 0 else "Never"
        
        # Generate encoded link
        enc_id = await encode(f"inv_{ch_id}")
        bot_link = f"https://t.me/{client.username}?start={enc_id}"
        
        return await temp.edit(
            f"<b>⚠️ Channel already has an invite link!</b>\n\n"
            f"<b>Channel ID:</b> <code>{ch_id}</code>\n"
            f"<b>Current Mode:</b> {mode}\n"
            f"<b>Expiry:</b> {expiry}\n\n"
            f"<b>🔗 Existing Link:</b>\n<code>{bot_link}</code>\n\n"
            f"<i>💡 Tip: Use /remove_invite to delete it first, or use /invite_mode to change settings.</i>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Share Link", url=f'https://telegram.me/share/url?url={bot_link}')],
                [InlineKeyboardButton("Close ✖️", callback_data="close")]
            ])
        )
    
    try:
        # Get channel info
        chat = await client.get_chat(ch_id)
        
        # Check bot permissions
        member = await client.get_chat_member(ch_id, "me")
        if not member.privileges or not member.privileges.can_invite_users:
            return await temp.edit(
                "<b>❌ Bot needs 'Invite Users' permission in this channel!</b>"
            )
        
        # Add to database with default settings
        await db.add_invite_link(ch_id)
        
        # Set default mode to 'request'
        await db.set_invite_mode(ch_id, "request")
        
        # Generate encoded link
        enc_id = await encode(f"inv_{ch_id}")
        bot_link = f"https://t.me/{client.username}?start={enc_id}"
        
        await temp.edit(
            f"<b>✅ Invite link generated successfully!</b>\n\n"
            f"<b>Channel:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{ch_id}</code>\n"
            f"<b>Mode:</b> 🟢 Request (Default)\n"
            f"<b>Expiry:</b> Never (Default)\n\n"
            f"<b>🔗 Bot Link:</b>\n<code>{bot_link}</code>\n\n"
            f"<i>💡 Use /invite_mode to change mode or /set_expiry to set expiration.</i>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Share Link", url=f'https://telegram.me/share/url?url={bot_link}')],
                [InlineKeyboardButton("Close ✖️", callback_data="close")]
            ])
        )
        
    except ChannelPrivate:
        await temp.edit("<b>❌ Bot is not a member of this channel!</b>")
    except ChatAdminRequired:
        await temp.edit("<b>❌ Bot must be an admin with 'Invite Users' permission!</b>")
    except PeerIdInvalid:
        await temp.edit("<b>❌ Invalid Channel ID!</b>")
    except Exception as e:
        await temp.edit(f"<b>❌ Error:</b> <code>{str(e)}</code>")


# ==================== REMOVE INVITE LINK ====================
@Bot.on_message(filters.command('remove_invite') & filters.private & admin)
async def remove_invite_link(client: Client, message: Message):
    """
    Command: /remove_invite <channel_id | all>
    Removes invite link from database
    """
    temp = await message.reply("<b><i>Processing...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)
    
    if len(args) != 2:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>Format:</b> <code>/remove_invite &lt;channel_id | all&gt;</code>\n"
            "<b>Examples:</b>\n"
            "<code>/remove_invite -1001234567890</code>\n"
            "<code>/remove_invite all</code>"
        )
    
    # Remove all links
    if args[1].lower() == "all":
        all_links = await db.get_all_invite_links()
        if not all_links:
            return await temp.edit("<b>❌ No invite links found in database!</b>")
        
        for ch_id in all_links:
            await db.remove_invite_link(ch_id)
        
        return await temp.edit(
            f"<b>✅ Successfully removed {len(all_links)} invite link(s)!</b>"
        )
    
    # Remove specific link
    try:
        ch_id = int(args[1])
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID format!</b>")
    
    if not await db.invite_link_exist(ch_id):
        return await temp.edit(
            f"<b>❌ No invite link found for this channel!</b>\n\n"
            f"<b>Channel ID:</b> <code>{ch_id}</code>"
        )
    
    try:
        chat = await client.get_chat(ch_id)
        ch_name = chat.title
    except:
        ch_name = f"ID: {ch_id}"
    
    await db.remove_invite_link(ch_id)
    await temp.edit(
        f"<b>✅ Invite link removed successfully!</b>\n\n"
        f"<b>Channel:</b> {ch_name}\n"
        f"<b>ID:</b> <code>{ch_id}</code>"
    )


# ==================== LIST INVITE LINKS ====================
@Bot.on_message(filters.command('list_invites') & filters.private & admin)
async def list_invite_links(client: Client, message: Message):
    """
    Command: /list_invites
    Shows all channels with invite links
    """
    temp = await message.reply("<b><i>Fetching invite links...</i></b>", quote=True)
    
    all_links = await db.get_all_invite_links()
    
    if not all_links:
        return await temp.edit("<b>❌ No invite links found in database!</b>")
    
    result = "<b>📋 Active Invite Links:</b>\n\n"
    
    for i, ch_id in enumerate(all_links, 1):
        try:
            chat = await client.get_chat(ch_id)
            settings = await db.get_invite_settings(ch_id)
            mode = "🟢 Request" if settings['mode'] == "request" else "🔵 Normal"
            expiry = f"{settings['expiry']}s" if settings['expiry'] > 0 else "Never"
            
            enc_id = await encode(f"inv_{ch_id}")
            bot_link = f"https://t.me/{client.username}?start={enc_id}"
            
            result += (
                f"<b>{i}.</b> {chat.title}\n"
                f"   <b>ID:</b> <code>{ch_id}</code>\n"
                f"   <b>Mode:</b> {mode}\n"
                f"   <b>Expiry:</b> {expiry}\n"
                f"   <b>Link:</b> <code>{bot_link}</code>\n\n"
            )
        except Exception as e:
            result += (
                f"<b>{i}.</b> <code>{ch_id}</code> (Unavailable)\n"
                f"   <i>Error: {str(e)[:50]}</i>\n\n"
            )
    
    await temp.edit(
        result,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
    )


# ==================== MANAGE LINK MODE (COMMAND-BASED) ====================
@Bot.on_message(filters.command('invite_mode') & filters.private & admin)
async def manage_invite_mode(client: Client, message: Message):
    """
    Command: /invite_mode <channel_id> <on/off>
    Toggle invite link mode - 'on' for request mode, 'off' for normal mode
    """
    temp = await message.reply("<b><i>Processing...</i></b>", quote=True)
    args = message.text.split()
    
    # If no arguments, show list of channels with their modes
    if len(args) == 1:
        all_links = await db.get_all_invite_links()
        
        if not all_links:
            return await temp.edit("<b>❌ No invite links found!</b>\n\n<i>Use /add_invite to create one.</i>")
        
        result = "<b>⚙️ Invite Link Modes:</b>\n\n"
        
        for i, ch_id in enumerate(all_links, 1):
            try:
                chat = await client.get_chat(ch_id)
                settings = await db.get_invite_settings(ch_id)
                mode_icon = "🟢" if settings['mode'] == "request" else "🔵"
                mode_text = "Request (ON)" if settings['mode'] == "request" else "Normal (OFF)"
                
                result += (
                    f"<b>{i}.</b> {chat.title}\n"
                    f"   <b>ID:</b> <code>{ch_id}</code>\n"
                    f"   <b>Mode:</b> {mode_icon} {mode_text}\n\n"
                )
            except Exception as e:
                result += (
                    f"<b>{i}.</b> <code>{ch_id}</code> (Unavailable)\n\n"
                )
        
        result += (
            "<b>💡 Usage:</b>\n"
            "<code>/invite_mode &lt;channel_id&gt; &lt;on|off&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/invite_mode -1001234567890 on</code>\n"
            "<code>/invite_mode -1001234567890 off</code>\n\n"
            "<i>• <b>ON</b> = 🟢 Request Mode (Join requests)\n"
            "• <b>OFF</b> = 🔵 Normal Mode (Direct invite)</i>"
        )
        
        return await temp.edit(
            result,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        )
    
    # If arguments provided, toggle the mode
    if len(args) != 3:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>Format:</b> <code>/invite_mode &lt;channel_id&gt; &lt;on|off&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/invite_mode -1001234567890 on</code> (Request Mode)\n"
            "<code>/invite_mode -1001234567890 off</code> (Normal Mode)\n\n"
            "<i>• <b>ON</b> = 🟢 Request Mode\n"
            "• <b>OFF</b> = 🔵 Normal Mode</i>"
        )
    
    try:
        ch_id = int(args[1])
        mode_input = args[2].lower()
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID format!</b>")
    
    if mode_input not in ['on', 'off']:
        return await temp.edit(
            "<b>❌ Invalid mode!</b>\n\n"
            "Use <code>on</code> for Request Mode or <code>off</code> for Normal Mode"
        )
    
    if not await db.invite_link_exist(ch_id):
        return await temp.edit(
            f"<b>❌ No invite link found for channel <code>{ch_id}</code></b>\n\n"
            "<i>Use /add_invite first.</i>"
        )
    
    # Set mode
    new_mode = "request" if mode_input == "on" else "normal"
    await db.set_invite_mode(ch_id, new_mode)
    
    # Get channel name
    try:
        chat = await client.get_chat(ch_id)
        ch_name = chat.title
    except:
        ch_name = f"ID: {ch_id}"
    
    mode_display = "🟢 Request Mode (ON)" if new_mode == "request" else "🔵 Normal Mode (OFF)"
    
    await temp.edit(
        f"<b>✅ Mode updated successfully!</b>\n\n"
        f"<b>Channel:</b> {ch_name}\n"
        f"<b>ID:</b> <code>{ch_id}</code>\n"
        f"<b>New Mode:</b> {mode_display}"
    )


# ==================== SET LINK EXPIRY ====================
@Bot.on_message(filters.command('set_expiry') & filters.private & admin)
async def set_link_expiry(client: Client, message: Message):
    """
    Command: /set_expiry <channel_id> <seconds>
    Sets expiry time for invite links (0 = never expire)
    """
    temp = await message.reply("<b><i>Processing...</i></b>", quote=True)
    args = message.text.split()
    
    if len(args) != 3:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>Format:</b> <code>/set_expiry &lt;channel_id&gt; &lt;seconds&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/set_expiry -1001234567890 3600</code> (1 hour)\n"
            "<code>/set_expiry -1001234567890 0</code> (never expire)\n\n"
            "<b>Common values:</b>\n"
            "• 3600 = 1 hour\n"
            "• 86400 = 1 day\n"
            "• 604800 = 1 week\n"
            "• 0 = Never expire"
        )
    
    try:
        ch_id = int(args[1])
        expiry = int(args[2])
    except ValueError:
        return await temp.edit("<b>❌ Invalid format! Use integers only.</b>")
    
    if expiry < 0:
        return await temp.edit("<b>❌ Expiry time cannot be negative!</b>")
    
    if not await db.invite_link_exist(ch_id):
        return await temp.edit(
            f"<b>❌ No invite link found for channel <code>{ch_id}</code></b>\n\n"
            "<i>Use /add_invite first.</i>"
        )
    
    await db.set_invite_expiry(ch_id, expiry)
    
    try:
        chat = await client.get_chat(ch_id)
        ch_name = chat.title
    except:
        ch_name = f"ID: {ch_id}"
    
    expiry_text = "Never expire" if expiry == 0 else f"{expiry} seconds"
    
    await temp.edit(
        f"<b>✅ Expiry time updated successfully!</b>\n\n"
        f"<b>Channel:</b> {ch_name}\n"
        f"<b>ID:</b> <code>{ch_id}</code>\n"
        f"<b>Expiry:</b> {expiry_text}"
    )


# ==================== AUTO APPROVE REQUESTS ====================
@Bot.on_message(filters.command('approve_req') & filters.private & admin)
async def manage_auto_approve(client: Client, message: Message):
    """
    Command: /approve_req <channel_id> <on/off>
    Enable/disable auto-approval of join requests
    """
    temp = await message.reply("<b><i>Processing...</i></b>", quote=True)
    args = message.text.split()
    
    # If no arguments, show list of channels with auto-approve status
    if len(args) == 1:
        all_links = await db.get_all_invite_links()
        
        if not all_links:
            return await temp.edit("<b>❌ No invite links found!</b>\n\n<i>Use /add_invite to create one.</i>")
        
        result = "<b>🤖 Auto-Approve Status:</b>\n\n"
        
        for i, ch_id in enumerate(all_links, 1):
            try:
                chat = await client.get_chat(ch_id)
                auto_approve = await db.get_auto_approve(ch_id)
                status_icon = "✅" if auto_approve else "❌"
                status_text = "Enabled (ON)" if auto_approve else "Disabled (OFF)"
                
                result += (
                    f"<b>{i}.</b> {chat.title}\n"
                    f"   <b>ID:</b> <code>{ch_id}</code>\n"
                    f"   <b>Auto-Approve:</b> {status_icon} {status_text}\n\n"
                )
            except Exception as e:
                result += (
                    f"<b>{i}.</b> <code>{ch_id}</code> (Unavailable)\n\n"
                )
        
        result += (
            "<b>💡 Usage:</b>\n"
            "<code>/approve_req &lt;channel_id&gt; &lt;on|off&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/approve_req -1001234567890 on</code>\n"
            "<code>/approve_req -1001234567890 off</code>\n\n"
            "<i>• <b>ON</b> = ✅ Auto-approve join requests\n"
            "• <b>OFF</b> = ❌ Manual approval required</i>"
        )
        
        return await temp.edit(
            result,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        )
    
    # If arguments provided, toggle auto-approve
    if len(args) != 3:
        return await temp.edit(
            "<b>❌ Invalid Usage!</b>\n\n"
            "<b>Format:</b> <code>/approve_req &lt;channel_id&gt; &lt;on|off&gt;</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/approve_req -1001234567890 on</code> (Enable auto-approve)\n"
            "<code>/approve_req -1001234567890 off</code> (Disable auto-approve)\n\n"
            "<i>• <b>ON</b> = ✅ Auto-approve\n"
            "• <b>OFF</b> = ❌ Manual approval</i>"
        )
    
    try:
        ch_id = int(args[1])
        mode_input = args[2].lower()
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID format!</b>")
    
    if mode_input not in ['on', 'off']:
        return await temp.edit(
            "<b>❌ Invalid mode!</b>\n\n"
            "Use <code>on</code> to enable or <code>off</code> to disable auto-approve"
        )
    
    if not await db.invite_link_exist(ch_id):
        return await temp.edit(
            f"<b>❌ No invite link found for channel <code>{ch_id}</code></b>\n\n"
            "<i>Use /add_invite first.</i>"
        )
    
    # Set auto-approve
    enabled = mode_input == "on"
    await db.set_auto_approve(ch_id, enabled)
    
    # Get channel name
    try:
        chat = await client.get_chat(ch_id)
        ch_name = chat.title
    except:
        ch_name = f"ID: {ch_id}"
    
    status_display = "✅ Enabled (ON)" if enabled else "❌ Disabled (OFF)"
    
    await temp.edit(
        f"<b>✅ Auto-approve updated successfully!</b>\n\n"
        f"<b>Channel:</b> {ch_name}\n"
        f"<b>ID:</b> <code>{ch_id}</code>\n"
        f"<b>Auto-Approve:</b> {status_display}\n\n"
        f"<i>{'Bot will now automatically approve join requests and notify users.' if enabled else 'Join requests will require manual approval.'}</i>"
    )


# ==================== AUTO APPROVE HANDLER ====================
@Bot.on_chat_join_request()
async def handle_join_request_approval(client: Client, chat_join_request):
    """
    Automatically approve join requests if auto-approve is enabled
    """
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id
    user_name = chat_join_request.from_user.first_name
    
    # Check if this channel has an invite link with auto-approve enabled
    if await db.invite_link_exist(chat_id):
        auto_approve = await db.get_auto_approve(chat_id)
        
        if auto_approve:
            try:
                # Approve the join request
                await client.approve_chat_join_request(chat_id, user_id)
                
                # Get channel name
                try:
                    chat = await client.get_chat(chat_id)
                    ch_name = chat.title
                except:
                    ch_name = "the channel"
                
                # Send notification to user (without channel link)
                try:
                    await client.send_message(
                        user_id,
                        f"<b>🎉 Request Approved!</b>\n\n"
                        f"<b>Your join request has been approved for:</b>\n"
                        f"<b>{ch_name}</b>\n\n"
                        f"<i>You can now access the channel content.</i>",
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    print(f"[AUTO-APPROVE] Failed to send notification to {user_id}: {e}")
                
                print(f"[AUTO-APPROVE] Approved {user_name} ({user_id}) for {ch_name} ({chat_id})")
                
            except Exception as e:
                print(f"[AUTO-APPROVE ERROR] Failed to approve {user_id} for {chat_id}: {e}")
