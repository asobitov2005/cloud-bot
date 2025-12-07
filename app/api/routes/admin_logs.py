from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.api.auth import require_super_admin
from app.models.base import AdminUser
import json


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ==================== WEB PAGE ====================

@router.get("/logs", response_class=HTMLResponse)
async def admin_logs_page(
    request: Request,
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Admin audit logs page (super admin only, read-only)"""
    return templates.TemplateResponse("admin_logs.html", {
        "request": request,
        "current_admin": current_admin
    })


# ==================== API ENDPOINT ====================

@router.get("/api/logs")
async def get_admin_logs(
    skip: int = 0,
    limit: int = 100,
    admin_id: Optional[int] = None,
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Get admin audit logs (super admin only, read-only)"""
    from app.models.crud import get_admin_logs, get_admin_logs_count, get_admin_by_id
    
    logs = await get_admin_logs(
        db,
        skip=skip,
        limit=limit,
        admin_id=admin_id,
        action_type=action_type
    )
    total = await get_admin_logs_count(db)
    
    # Get admin usernames for logs
    admin_cache = {}
    logs_data = []
    
    for log in logs:
        # Cache admin info
        if log.admin_id not in admin_cache:
            admin = await get_admin_by_id(db, log.admin_id)
            admin_cache[log.admin_id] = admin.username if admin else "Unknown"
        
        # Parse details JSON
        details = None
        if log.details:
            try:
                details = json.loads(log.details)
            except:
                details = log.details
        
        logs_data.append({
            "id": log.id,
            "admin_id": log.admin_id,
            "admin_username": admin_cache[log.admin_id],
            "action_type": log.action_type,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat()
        })
    
    return {
        "logs": logs_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }
