from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.crud import (
    get_users_count, get_files_count, get_total_downloads,
    get_top_downloaded_files, get_downloads_by_date, get_user_growth
)
from app.api.auth import verify_token, verify_web_token


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: dict = Depends(verify_web_token)):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get dashboard statistics"""
    users_count = await get_users_count(db)
    files_count = await get_files_count(db)
    downloads_count = await get_total_downloads(db)
    top_files = await get_top_downloaded_files(db, limit=5)
    downloads_data = await get_downloads_by_date(db, days=7)
    
    return {
        "total_users": users_count,
        "total_files": files_count,
        "total_downloads": downloads_count,
        "downloads_chart": {
            "labels": [row["date"] for row in downloads_data],
            "values": [row["count"] for row in downloads_data]
        },
        "top_files": [
            {
                "title": item["file"].title,
                "downloads": item["downloads"]
            }
            for item in top_files
        ]
    }
