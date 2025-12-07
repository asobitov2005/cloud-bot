from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.api.auth import require_super_admin, get_password_hash
from app.models.base import AdminUser, AdminRole


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


class CreateAdminRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str = "admin"  # "admin" or "super_admin"


# ==================== WEB PAGES ====================

@router.get("/admins", response_class=HTMLResponse)
async def admins_page(
    request: Request,
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Admin management page (super admin only)"""
    return templates.TemplateResponse("admins.html", {
        "request": request,
        "current_admin": current_admin
    })


# ==================== API ENDPOINTS ====================

@router.get("/api/admins")
async def get_admins(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Get all admins (super admin only)"""
    from app.models.crud import get_all_admins
    
    admins = await get_all_admins(db)
    
    return {
        "admins": [
            {
                "id": admin.id,
                "username": admin.username,
                "full_name": admin.full_name,
                "email": admin.email,
                "role": admin.role.value,
                "is_active": admin.is_active,
                "created_at": admin.created_at.isoformat(),
                "last_login": admin.last_login.isoformat() if admin.last_login else None
            }
            for admin in admins
        ]
    }


@router.post("/api/admins")
async def create_admin(
    request: Request,
    data: CreateAdminRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Create new admin (super admin only)"""
    from app.models.crud import get_admin_by_username, create_admin_user, log_admin_action
    
    # Check if username already exists
    existing = await get_admin_by_username(db, data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Validate role
    if data.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    
    role = AdminRole.SUPER_ADMIN if data.role == "super_admin" else AdminRole.ADMIN
    
    # Create admin
    new_admin = await create_admin_user(
        db,
        username=data.username,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        email=data.email,
        role=role
    )
    
    # Log action
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action_type="create_admin",
        target_type="admin",
        target_id=str(new_admin.id),
        details={
            "username": new_admin.username,
            "role": new_admin.role.value
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return {
        "id": new_admin.id,
        "username": new_admin.username,
        "role": new_admin.role.value,
        "message": "Admin created successfully"
    }


@router.delete("/api/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(require_super_admin)
):
    """Delete admin (super admin only)"""
    from app.models.crud import get_admin_by_id, delete_admin_user, log_admin_action
    
    # Cannot delete self
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Get admin to delete
    admin_to_delete = await get_admin_by_id(db, admin_id)
    if not admin_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Delete admin
    success = await delete_admin_user(db, admin_id)
    
    if success:
        # Log action
        await log_admin_action(
            db,
            admin_id=current_admin.id,
            action_type="delete_admin",
            target_type="admin",
            target_id=str(admin_id),
            details={
                "username": admin_to_delete.username,
                "role": admin_to_delete.role.value
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    
    return {"message": "Admin deleted successfully"}
