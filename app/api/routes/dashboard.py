from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.crud import (
    get_users_count, get_files_count, get_total_downloads,
    get_top_downloaded_files, get_downloads_by_date, get_user_growth,
    get_users_by_country, get_users_joined_stats,
    get_users_left_stats, get_total_files_volume, get_downloads_by_period,
    get_health_stats
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
    try:
        users_count = await get_users_count(db)
        files_count = await get_files_count(db)
        downloads_count = await get_total_downloads(db)
        top_files = await get_top_downloaded_files(db, limit=5)
        downloads_data = await get_downloads_by_date(db, days=7)
        user_growth_data = await get_user_growth(db, days=30)  # Show last 30 days of user growth
        user_country_data = await get_users_by_country(db)
        users_joined = await get_users_joined_stats(db)
        users_left = await get_users_left_stats(db)
        files_volume = await get_total_files_volume(db)
        downloads_by_period = await get_downloads_by_period(db)
        health_stats = await get_health_stats(db, days=30)
        
        return {
            "total_users": users_count,
            "total_files": files_count,
            "total_downloads": downloads_count,
            "total_files_volume": files_volume,
            "users_joined": users_joined,
            "users_left": users_left,
            "downloads_chart": {
                "labels": [row["date"] for row in downloads_data],
                "values": [row["count"] for row in downloads_data]
            },
            "downloads_by_period": downloads_by_period,
            "top_files": [
                {
                    "title": item["file"].title,
                    "downloads": item["downloads"]
                }
                for item in top_files
            ],
            "user_growth_chart": {
                "labels": [row["date"] for row in user_growth_data],
                "values": [row["count"] for row in user_growth_data]
            },
            "user_country_chart": {
                "labels": [row["country"] for row in user_country_data],
                "values": [row["count"] for row in user_country_data]
            },
            "health_stats": health_stats
        }
    except Exception as e:
        import logging
        logging.error(f"Error in get_dashboard_stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading dashboard stats: {str(e)}")
