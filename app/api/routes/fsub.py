from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.crud import (
    get_force_subscribe_channels,
    add_force_subscribe_channel,
    remove_force_subscribe_channel
)
from app.api.auth import verify_token, verify_web_token
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/fsub", response_class=HTMLResponse)
async def fsub_page(request: Request, user: dict = Depends(verify_web_token)):
    """Force subscribe channels management page"""
    return templates.TemplateResponse("fsub.html", {"request": request})


@router.get("/api/fsub")
async def get_fsub_channels(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get all force subscribe channels"""
    channels = await get_force_subscribe_channels(db)
    return {"channels": channels}


@router.post("/api/fsub")
async def add_fsub_channel(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Add a force subscribe channel"""
    data = await request.json()
    channel_id = data.get("channel_id") or None
    channel_username = data.get("channel_username") or None
    channel_title = data.get("channel_title") or None
    invite_link = data.get("invite_link") or None
    
    # Convert empty strings to None
    if channel_id == "":
        channel_id = None
    if channel_username == "":
        channel_username = None
    if channel_title == "":
        channel_title = None
    if invite_link == "":
        invite_link = None
    
    # Handle case where channel_id is provided as a username string (e.g. "@username")
    if channel_id:
        try:
            # Try to convert to int to check if it's a valid ID
            int(channel_id)
        except (ValueError, TypeError):
            # If not an integer, treat as username if not already provided
            if not channel_username:
                channel_username = str(channel_id)
            channel_id = None
    
    # Try to get channel_id from username if not provided
    if not channel_id and channel_username:
        try:
            from app.bot.main import _bot_instance
            from aiogram.exceptions import ClientDecodeError
            import aiohttp
            
            if not _bot_instance:
                raise HTTPException(status_code=500, detail="Bot instance not available. Please try again.")
            # Remove @ if present
            username = channel_username.replace("@", "").strip()
            if not username:
                raise HTTPException(status_code=400, detail="Invalid username format")
            
            try:
                chat = await _bot_instance.get_chat(f"@{username}")
                if chat.type == "channel":
                    channel_id = chat.id
                    if not channel_title:
                        channel_title = chat.title
                    if not channel_username:
                        channel_username = chat.username
                else:
                    raise HTTPException(status_code=400, detail=f"@{username} is not a channel")
            except ClientDecodeError:
                # Channel has new features that aiogram can't parse - use raw API
                bot_token = _bot_instance.token
                url = f"https://api.telegram.org/bot{bot_token}/getChat"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json={"chat_id": f"@{username}"}) as resp:
                        raw_response = await resp.json()
                        if raw_response.get("ok"):
                            result = raw_response.get("result", {})
                            if result.get("type") == "channel":
                                channel_id = result.get("id")
                                if not channel_title:
                                    channel_title = result.get("title", f"@{username}")
                                if not channel_username:
                                    channel_username = result.get("username")
                            else:
                                raise HTTPException(status_code=400, detail=f"@{username} is not a channel")
                        else:
                            raise HTTPException(status_code=400, detail=f"Channel @{username} not found")
        except HTTPException:
            raise
        except Exception as e:
            # Log error but continue to try invite link
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not get channel from username {channel_username}: {e}")
    
    # Try to extract channel_id from invite link if it's a public channel link
    if not channel_id and invite_link:
        if "/c/" in invite_link:
            # Public channel link format: t.me/c/CHANNEL_ID/POST_ID
            try:
                parts = invite_link.split("/c/")
                if len(parts) > 1:
                    channel_part = parts[1].split("/")[0]
                    possible_id = int(channel_part)
                    # Try with -100 prefix (standard channel ID format)
                    channel_id = -1000000000000 + possible_id if possible_id < 1000000000000 else possible_id
                    # Try to get channel info
                    from app.bot.main import _bot_instance
                    from aiogram.exceptions import ClientDecodeError
                    import aiohttp
                    
                    if not _bot_instance:
                        raise HTTPException(status_code=500, detail="Bot instance not available. Please try again.")
                    
                    try:
                        chat = await _bot_instance.get_chat(channel_id)
                        if chat.type == "channel":
                            channel_id = chat.id
                            if not channel_title:
                                channel_title = chat.title
                            if not channel_username:
                                channel_username = chat.username
                        else:
                            raise HTTPException(status_code=400, detail="Invalid channel link")
                    except ClientDecodeError:
                        # Channel has new features - use raw API
                        bot_token = _bot_instance.token
                        url = f"https://api.telegram.org/bot{bot_token}/getChat"
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, json={"chat_id": channel_id}) as resp:
                                raw_response = await resp.json()
                                if raw_response.get("ok"):
                                    result = raw_response.get("result", {})
                                    if result.get("type") == "channel":
                                        channel_id = result.get("id")
                                        if not channel_title:
                                            channel_title = result.get("title", f"Channel {channel_id}")
                                        if not channel_username:
                                            channel_username = result.get("username")
                                    else:
                                        raise HTTPException(status_code=400, detail="Invalid channel link")
                                else:
                                    raise HTTPException(status_code=400, detail="Channel not found")
                    except HTTPException:
                        raise
                    except Exception:
                        # Try without prefix
                        try:
                            chat = await _bot_instance.get_chat(possible_id)
                            if chat.type == "channel":
                                channel_id = chat.id
                                if not channel_title:
                                    channel_title = chat.title
                                if not channel_username:
                                    channel_username = chat.username
                            else:
                                raise HTTPException(status_code=400, detail="Invalid channel link")
                        except ClientDecodeError:
                            # Try raw API with possible_id
                            bot_token = _bot_instance.token
                            url = f"https://api.telegram.org/bot{bot_token}/getChat"
                            async with aiohttp.ClientSession() as session:
                                async with session.post(url, json={"chat_id": possible_id}) as resp:
                                    raw_response = await resp.json()
                                    if raw_response.get("ok"):
                                        result = raw_response.get("result", {})
                                        if result.get("type") == "channel":
                                            channel_id = result.get("id")
                                            if not channel_title:
                                                channel_title = result.get("title", f"Channel {channel_id}")
                                            if not channel_username:
                                                channel_username = result.get("username")
                                        else:
                                            raise HTTPException(status_code=400, detail="Invalid channel link")
                                    else:
                                        raise HTTPException(status_code=400, detail="Channel not found")
                        except HTTPException:
                            raise
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Could not get channel from invite link {invite_link}: {e}")
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid invite link format")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error processing invite link {invite_link}: {e}")
    
    if not channel_id:
        raise HTTPException(status_code=400, detail="Channel ID is required. Please provide channel ID, username, or a public channel invite link (t.me/c/...)")
    
    success = await add_force_subscribe_channel(
        db,
        channel_id=int(channel_id),
        channel_username=channel_username,
        channel_title=channel_title,
        invite_link=invite_link
    )
    
    if success:
        return {"success": True, "message": "Channel added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Channel already exists")


@router.delete("/api/fsub/{channel_id}")
async def remove_fsub_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Remove a force subscribe channel"""
    success = await remove_force_subscribe_channel(db, channel_id)
    
    if success:
        return {"success": True, "message": "Channel removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Channel not found")

