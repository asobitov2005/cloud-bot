from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, ClientDecodeError
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.translations import get_text
from app.bot.keyboards.inline import get_remove_fsub_keyboard
from app.models.crud import (
    get_force_subscribe_channels, 
    add_force_subscribe_channel,
    remove_force_subscribe_channel
)
import logging
import aiohttp

logger = logging.getLogger(__name__)

router = Router()


class FSubStates(StatesGroup):
    waiting_for_channel = State()


@router.message(Command("fsub"))
async def cmd_fsub(message: Message, lang: str, db: AsyncSession):
    """Show all force subscribe channels"""
    channels = await get_force_subscribe_channels(db)
    
    if not channels:
        await message.answer(get_text("no_fsub_channels", lang))
        return
    
    # Build channels list
    channels_text = get_text("fsub_channels_list", lang) + "\n\n"
    for idx, channel in enumerate(channels, 1):
        channel_id = channel.get("channel_id")
        channel_username = channel.get("channel_username", "")
        channel_title = channel.get("channel_title", "")
        
        # Format channel display
        if channel_username:
            display = f"@{channel_username}"
        elif channel_title:
            display = channel_title
        else:
            display = f"Channel {channel_id}"
        
        channels_text += f"{idx}. {display}\n"
    
    # Send with inline keyboard for removal
    keyboard = get_remove_fsub_keyboard(channels, lang)
    await message.answer(channels_text, reply_markup=keyboard)


@router.message(Command("add_fsub"))
async def cmd_add_fsub(message: Message, state: FSMContext, lang: str):
    """Start adding a force subscribe channel"""
    await message.answer(get_text("add_fsub_instruction", lang))
    await state.set_state(FSubStates.waiting_for_channel)


@router.message(FSubStates.waiting_for_channel)
async def receive_fsub_channel(message: Message, state: FSMContext, db: AsyncSession, lang: str, db_user):
    """Receive and process channel to add"""
    channel_id = None
    channel_username = None
    channel_title = None
    
    # Check if message contains a channel forward or channel mention
    if message.forward_from_chat:
        # Forwarded from a channel
        chat = message.forward_from_chat
        if chat.type == "channel":
            channel_id = chat.id
            channel_username = chat.username
            channel_title = chat.title
    elif message.text:
        # Try to parse channel username, ID, or invite link from text
        text = message.text.strip()
        
        # Check if it's an invite link (t.me/joinchat or t.me/+ or t.me/c/)
        if "t.me/" in text or "telegram.me/" in text:
            # Extract invite link
            invite_link = text
            if "telegram.me/" in invite_link:
                invite_link = invite_link.replace("telegram.me/", "t.me/")
            
            # Try to get chat info from invite link
            try:
                # For invite links, we need to resolve them first
                # Telegram API doesn't directly support resolving invite links in getChat
                # But we can try to extract channel info if it's a public channel link
                if "/joinchat/" in invite_link or "/+" in invite_link:
                    # This is a private invite link - we can't get channel info directly from the link
                    # But we can store the invite link and ask for channel info separately
                    # Store the invite link temporarily in state
                    await state.update_data(invite_link=invite_link)
                    await message.answer(
                        "✅ Invite link detected!\n\n"
                        "Now please provide the channel information:\n"
                        "• Forward a message from the channel, OR\n"
                        "• Send channel username (e.g., @channelname), OR\n"
                        "• Send channel ID (e.g., -1001234567890)"
                    )
                    return
                elif "/c/" in invite_link:
                    # Public channel link format: t.me/c/CHANNEL_ID/POST_ID
                    # Extract channel ID from link
                    parts = invite_link.split("/c/")
                    if len(parts) > 1:
                        channel_part = parts[1].split("/")[0]
                        # Try to parse as channel ID
                        try:
                            # Channel IDs in links are without the -100 prefix
                            # Try both with and without prefix
                            possible_id = int(channel_part)
                            # Try with -100 prefix (standard channel ID format)
                            channel_id = -1000000000000 + possible_id if possible_id < 1000000000000 else possible_id
                            # Try to get channel info
                            try:
                                chat = await message.bot.get_chat(channel_id)
                                if chat.type == "channel":
                                    channel_id = chat.id
                                    channel_username = chat.username
                                    channel_title = chat.title
                            except (TelegramBadRequest, ClientDecodeError):
                                # Try without prefix
                                try:
                                    chat = await message.bot.get_chat(possible_id)
                                    if chat.type == "channel":
                                        channel_id = chat.id
                                        channel_username = chat.username
                                        channel_title = chat.title
                                except Exception:
                                    await message.answer("❌ Could not resolve channel from invite link. Please forward a message from the channel or provide channel ID.")
                                    return
                        except ValueError:
                            await message.answer("❌ Invalid invite link format. Please forward a message from the channel or provide channel ID.")
                            return
                    else:
                        await message.answer("❌ Invalid invite link format. Please forward a message from the channel or provide channel ID.")
                        return
                else:
                    # Try to extract username from link (t.me/username)
                    username_part = invite_link.split("t.me/")[-1].split("/")[0].split("?")[0]
                    if username_part.startswith("@"):
                        username_part = username_part[1:]
                    # Treat as username
                    channel_username = username_part
                    try:
                        chat = await message.bot.get_chat(f"@{channel_username}")
                        if chat.type == "channel":
                            channel_id = chat.id
                            channel_title = chat.title
                    except (TelegramBadRequest, ClientDecodeError) as e:
                        if isinstance(e, ClientDecodeError):
                            # Try raw API call
                            try:
                                bot_token = message.bot.token
                                url = f"https://api.telegram.org/bot{bot_token}/getChat"
                                async with aiohttp.ClientSession() as session:
                                    async with session.post(url, json={"chat_id": f"@{channel_username}"}) as resp:
                                        raw_response = await resp.json()
                                        if raw_response.get("ok"):
                                            result = raw_response.get("result", {})
                                            if result.get("type") == "channel":
                                                channel_id = result.get("id")
                                                channel_title = result.get("title", f"@{channel_username}")
                                            else:
                                                await message.answer("❌ This is not a channel.")
                                                return
                                        else:
                                            await message.answer("❌ Channel not found.")
                                            return
                            except Exception:
                                await message.answer("❌ Could not get channel info. Please forward a message from the channel.")
                                return
                        else:
                            await message.answer(get_text("fsub_channel_not_found", lang))
                            return
            except Exception as e:
                logger.error(f"Error processing invite link: {e}")
                await message.answer("❌ Error processing invite link. Please forward a message from the channel or provide channel ID.")
                return
        
        # Check if it's a channel username (starts with @)
        elif text.startswith("@"):
            channel_username = text[1:]
            # Try to get channel info
            try:
                chat = await message.bot.get_chat(f"@{channel_username}")
                if chat.type == "channel":
                    channel_id = chat.id
                    channel_title = chat.title
            except ClientDecodeError as e:
                # ClientDecodeError can occur with newer Telegram API features (e.g., paid reactions)
                # The channel exists but aiogram can't parse the response
                # Try to extract basic info from the raw JSON response in the exception
                logger.warning(f"ClientDecodeError when getting channel @{channel_username}: {e}")
                try:
                    # ClientDecodeError has json_data in its args or as attribute
                    raw_data = None
                    if hasattr(e, 'json_data'):
                        raw_data = e.json_data
                    elif hasattr(e, 'args') and len(e.args) > 2:
                        raw_data = e.args[2]  # json_data is usually the 3rd argument
                    
                    # Extract channel info from raw JSON
                    if raw_data and isinstance(raw_data, dict):
                        if raw_data.get("ok"):
                            result = raw_data.get("result", {})
                            if result.get("type") == "channel":
                                channel_id = result.get("id")
                                channel_title = result.get("title", f"@{channel_username}")
                                # We have the info we need, continue with adding the channel
                                logger.info(f"Successfully extracted channel info from raw JSON: ID={channel_id}, Title={channel_title}")
                            else:
                                await message.answer("❌ This is not a channel. Please provide a channel username or ID.")
                                return
                        else:
                            raise Exception("API returned error")
                    else:
                        # Try to make a raw API call that bypasses parsing
                        bot_token = message.bot.token
                        url = f"https://api.telegram.org/bot{bot_token}/getChat"
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, json={"chat_id": f"@{channel_username}"}) as resp:
                                raw_response = await resp.json()
                                if raw_response.get("ok"):
                                    result = raw_response.get("result", {})
                                    if result.get("type") == "channel":
                                        channel_id = result.get("id")
                                        channel_title = result.get("title", f"@{channel_username}")
                                        logger.info(f"Successfully got channel info via raw API: ID={channel_id}, Title={channel_title}")
                                    else:
                                        await message.answer("❌ This is not a channel. Please provide a channel username or ID.")
                                        return
                                else:
                                    raise Exception("API returned error")
                except Exception as extract_error:
                    logger.error(f"Could not extract channel info from ClientDecodeError: {extract_error}")
                    await message.answer(
                        f"⚠️ Channel @{channel_username} found but couldn't parse full info (channel may have new features).\n\n"
                        f"Please forward a message from the channel instead - this will work reliably.\n"
                        f"Or provide the channel ID directly (e.g., -1001234567890)."
                    )
                    return
            except TelegramBadRequest:
                await message.answer(get_text("fsub_channel_not_found", lang))
                return
        else:
            # Try to parse as channel ID
            try:
                channel_id = int(text)
                # Try to get channel info
                try:
                    chat = await message.bot.get_chat(channel_id)
                    if chat.type == "channel":
                        channel_id = chat.id
                        channel_username = chat.username
                        channel_title = chat.title
                except ClientDecodeError as e:
                    # ClientDecodeError can occur with newer Telegram API features (e.g., paid reactions)
                    # The channel exists but aiogram can't parse the response
                    logger.warning(f"ClientDecodeError when getting channel {channel_id}: {e}")
                    try:
                        # Try to extract info from raw JSON or make raw API call
                        raw_data = None
                        if hasattr(e, 'json_data'):
                            raw_data = e.json_data
                        elif hasattr(e, 'args') and len(e.args) > 2:
                            raw_data = e.args[2]
                        
                        if raw_data and isinstance(raw_data, dict) and raw_data.get("ok"):
                            result = raw_data.get("result", {})
                            if result.get("type") == "channel":
                                channel_id = result.get("id")
                                channel_title = result.get("title", f"Channel {channel_id}")
                                channel_username = result.get("username")
                                logger.info(f"Successfully extracted channel info from raw JSON: ID={channel_id}")
                            else:
                                await message.answer("❌ This is not a channel. Please provide a channel ID.")
                                return
                        else:
                            # Try raw API call
                            bot_token = message.bot.token
                            url = f"https://api.telegram.org/bot{bot_token}/getChat"
                            async with aiohttp.ClientSession() as session:
                                async with session.post(url, json={"chat_id": channel_id}) as resp:
                                    raw_response = await resp.json()
                                    if raw_response.get("ok"):
                                        result = raw_response.get("result", {})
                                        if result.get("type") == "channel":
                                            channel_id = result.get("id")
                                            channel_title = result.get("title", f"Channel {channel_id}")
                                            channel_username = result.get("username")
                                            logger.info(f"Successfully got channel info via raw API: ID={channel_id}")
                                        else:
                                            await message.answer("❌ This is not a channel. Please provide a channel ID.")
                                            return
                                    else:
                                        raise Exception("API returned error")
                    except Exception as extract_error:
                        logger.error(f"Could not extract channel info: {extract_error}")
                        # Use provided ID and allow adding without full info
                        channel_title = f"Channel {channel_id}"
                        logger.info(f"Using provided channel ID {channel_id} without full info")
                except TelegramBadRequest:
                    await message.answer(get_text("fsub_channel_not_found", lang))
                    return
            except ValueError:
                await message.answer(get_text("fsub_invalid_format", lang))
                return
    
    # Check if there's an invite link stored in state (from previous message)
    state_data = await state.get_data()
    invite_link = state_data.get("invite_link")
    
    # Also check if there's an invite link in the current message (entities or text)
    if not invite_link:
        if message.entities:
            for entity in message.entities:
                if entity.type == "url" or entity.type == "text_link":
                    url = entity.url if hasattr(entity, 'url') else message.text[entity.offset:entity.offset + entity.length]
                    if ("t.me/" in url or "telegram.me/" in url) and ("/joinchat/" in url or "/+" in url):
                        # This is an invite link
                        invite_link = url.replace("telegram.me/", "t.me/")
                        break
        
        # Also check if the text itself is an invite link
        if not invite_link and message.text:
            text_lower = message.text.lower()
            if ("t.me/" in text_lower or "telegram.me/" in text_lower) and ("/joinchat/" in text_lower or "/+" in text_lower):
                invite_link = message.text.strip().replace("telegram.me/", "t.me/")
    
    if not channel_id:
        await message.answer(get_text("fsub_invalid_format", lang))
        return
    
    # Add channel to force subscribe list
    success = await add_force_subscribe_channel(
        db, 
        channel_id=channel_id,
        channel_username=channel_username,
        channel_title=channel_title,
        invite_link=invite_link
    )
    
    if success:
        channel_display = channel_username and f"@{channel_username}" or (channel_title or str(channel_id))
        success_msg = get_text("fsub_channel_added", lang, channel=channel_display)
        if invite_link:
            success_msg += f"\n\n✅ Invite link saved: {invite_link}"
        await message.answer(success_msg)
    else:
        await message.answer(get_text("fsub_channel_exists", lang))
    
    # Clear state including invite_link
    await state.clear()


@router.callback_query(F.data.startswith("remove_fsub:"))
async def handle_remove_fsub(callback: CallbackQuery, lang: str, db: AsyncSession):
    """Handle remove force subscribe channel"""
    try:
        channel_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(get_text("delete_not_found", lang), show_alert=True)
        return
    
    # Remove channel
    success = await remove_force_subscribe_channel(db, channel_id)
    
    if success:
        await callback.answer(get_text("fsub_channel_removed", lang))
        
        # Refresh the list
        channels = await get_force_subscribe_channels(db)
        
        if not channels:
            await callback.message.edit_text(get_text("no_fsub_channels", lang))
        else:
            # Rebuild channels list
            channels_text = get_text("fsub_channels_list", lang) + "\n\n"
            for idx, channel in enumerate(channels, 1):
                channel_id_item = channel.get("channel_id")
                channel_username = channel.get("channel_username", "")
                channel_title = channel.get("channel_title", "")
                
                if channel_username:
                    display = f"@{channel_username}"
                elif channel_title:
                    display = channel_title
                else:
                    display = f"Channel {channel_id_item}"
                
                channels_text += f"{idx}. {display}\n"
            
            keyboard = get_remove_fsub_keyboard(channels, lang)
            await callback.message.edit_text(channels_text, reply_markup=keyboard)
    else:
        await callback.answer(get_text("delete_not_found", lang), show_alert=True)

