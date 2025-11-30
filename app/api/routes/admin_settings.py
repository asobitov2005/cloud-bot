from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.crud import get_setting, set_setting
from app.api.auth import verify_token, verify_web_token, get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: dict = Depends(verify_web_token)):
    """Admin settings page"""
    return templates.TemplateResponse("settings.html", {"request": request})


@router.get("/api/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get current admin settings"""
    admin_username = await get_setting(db, "admin_username")
    admin_display_username = await get_setting(db, "admin_display_username")
    
    # Don't return password hash for security
    return {
        "username": admin_username or "admin",
        "display_username": admin_display_username or "",
        "password_set": bool(await get_setting(db, "admin_password_hash"))
    }


@router.put("/api/settings/username")
async def update_username(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Update admin username"""
    data = await request.json()
    new_username = data.get("username", "").strip()
    
    if not new_username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    if len(new_username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    
    await set_setting(db, "admin_username", new_username)
    return {"success": True, "message": "Username updated successfully"}


@router.put("/api/settings/password")
async def update_password(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Update admin password"""
    data = await request.json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current password and new password are required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Verify current password
    admin_password_hash = await get_setting(db, "admin_password_hash")
    if not admin_password_hash:
        # If no password is set, allow setting it without current password
        pass
    else:
        if not verify_password(current_password, admin_password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash and save new password
    new_password_hash = get_password_hash(new_password)
    await set_setting(db, "admin_password_hash", new_password_hash)
    
    return {"success": True, "message": "Password updated successfully"}


@router.put("/api/settings/display-username")
async def update_display_username(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Update admin display username (shown in bot messages)"""
    data = await request.json()
    new_display_username = data.get("display_username", "").strip()
    
    # Allow empty to reset to default
    if new_display_username and len(new_display_username) < 1:
        raise HTTPException(status_code=400, detail="Display username must be at least 1 character")
    
    await set_setting(db, "admin_display_username", new_display_username if new_display_username else None)
    return {"success": True, "message": "Display username updated successfully"}

