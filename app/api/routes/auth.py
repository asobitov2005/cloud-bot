from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from app.api.auth import create_access_token, get_password_hash, verify_password
from app.core.config import settings


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    # Check credentials
    if username != settings.ADMIN_USERNAME or password != settings.ADMIN_PASSWORD:
        return RedirectResponse(url="/admin/login?error=1", status_code=303)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": username},
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
async def logout():
    """Logout"""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    return response
