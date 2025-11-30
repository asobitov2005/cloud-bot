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
    from app.models.permissions import parse_permissions
    
    users = await get_all_users(db, skip=skip, limit=limit, primary_admin_id=settings.ADMIN_ID)
    
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
                "permissions": parse_permissions(u.admin_permissions),
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
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Make user an admin with permissions"""
    data = await request.json()
    permissions = data.get("permissions", [])  # List of permission strings
    
    try:
        user = await toggle_admin_status(db, user_id, True, settings.ADMIN_ID, permissions=permissions)
        
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


@router.put("/api/users/{user_id}/permissions")
async def update_permissions_route(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Update admin permissions for a user"""
    data = await request.json()
    permissions = data.get("permissions", [])  # List of permission strings
    
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_admin:
            raise HTTPException(status_code=400, detail="User is not an admin")
        
        # Protect primary admin - cannot change their permissions
        if user.telegram_id == settings.ADMIN_ID:
            raise HTTPException(status_code=400, detail="Cannot change permissions for primary admin")
        
        # Update permissions
        from app.models.permissions import serialize_permissions
        user.admin_permissions = serialize_permissions(permissions) if permissions else None
        await db.commit()
        await db.refresh(user)
        
        return {"success": True, "message": "Permissions updated successfully"}
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


@router.get("/api/permissions")
async def get_permissions(
    token: dict = Depends(verify_token)
):
    """Get list of available permissions"""
    from app.models.permissions import PERMISSIONS
    return {
        "permissions": [{"key": k, "label": v} for k, v in PERMISSIONS.items()]
    }


