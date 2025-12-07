from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from datetime import timedelta
from app.api.auth import create_access_token, verify_password, get_current_admin
from app.core.config import settings
from app.models.base import AdminUser


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle admin login with audit logging"""
    from app.models.crud import get_admin_by_username, update_admin_last_login, log_admin_action
    
    # Get admin user from database
    admin = await get_admin_by_username(db, username)
    
    # Check if admin exists
    if not admin:
        return RedirectResponse(url="/admin/login?error=invalid", status_code=303)
    
    # Check if admin is active
    if not admin.is_active:
        return RedirectResponse(url="/admin/login?error=inactive", status_code=303)
    
    # Verify password
    if not verify_password(password, admin.password_hash):
        # Log failed login attempt
        await log_admin_action(
            db,
            admin_id=admin.id,
            action_type="login_failed",
            details={"reason": "invalid_password"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return RedirectResponse(url="/admin/login?error=invalid", status_code=303)
    
    # Update last login timestamp
    await update_admin_last_login(db, admin.id)
    
    # Log successful login
    await log_admin_action(
        db,
        admin_id=admin.id,
        action_type="login",
        details={"username": username},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Create access token with admin role
    access_token = create_access_token(
        data={
            "sub": username,
            "admin_id": admin.id,
            "role": admin.role.value
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Redirect to dashboard with token
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.get("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Logout with audit logging"""
    from app.models.crud import log_admin_action
    
    # Log logout
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action_type="logout",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response
