from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.core.database import get_db
from app.core.config import settings
from app.models.crud import (
    get_all_users, block_user, unblock_user, 
    toggle_admin_status, get_user_by_id
)
from app.api.auth import verify_token, verify_web_token


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, auth_result = Depends(verify_web_token)):
    """Users management page"""
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("users.html", {"request": request})


@router.get("/api/users")
async def get_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get users list"""
    users = await get_all_users(db, skip=skip, limit=limit)
    
    return {
        "users": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "full_name": u.full_name,
                "language": u.language,
                "is_blocked": u.is_blocked,
                "is_admin": u.is_admin,
                "is_primary_admin": u.telegram_id == settings.ADMIN_ID,
                "joined_at": u.joined_at.isoformat()
            }
            for u in users
        ]
    }


@router.post("/api/users/{user_id}/block")
async def block_user_route(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Block user"""
    await block_user(db, user_id)
    return {"success": True, "message": "User blocked successfully"}


@router.post("/api/users/{user_id}/unblock")
async def unblock_user_route(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Unblock user"""
    await unblock_user(db, user_id)
    return {"success": True, "message": "User unblocked successfully"}


@router.post("/api/users/{user_id}/make-admin")
async def make_admin_route(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Make user an admin"""
    try:
        user = await toggle_admin_status(db, user_id, True, settings.ADMIN_ID)
        
        # Update bot commands for this user
        from app.bot.main import update_user_commands
        try:
            await update_user_commands(user.telegram_id, is_admin=True)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update commands for new admin: {e}")
        
        return {"success": True, "message": "User promoted to admin"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/users/{user_id}/remove-admin")
async def remove_admin_route(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Remove admin rights from user"""
    try:
        user = await toggle_admin_status(db, user_id, False, settings.ADMIN_ID)
        
        # Update bot commands for this user
        from app.bot.main import update_user_commands
        try:
            await update_user_commands(user.telegram_id, is_admin=False)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to update commands for removed admin: {e}")
        
        return {"success": True, "message": "Admin rights removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


