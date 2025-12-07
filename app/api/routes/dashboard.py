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
    """Get dashboard statistics (optimized - removed Telegram API calls)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Note: SQLAlchemy async session doesn't support concurrent operations
        # So we execute queries sequentially, but removed slow Telegram API calls
        users_count = await get_users_count(db)
        files_count = await get_files_count(db)
        downloads_count = await get_total_downloads(db)
        
        # Get top files with error handling (file might be None if deleted)
        top_files = await get_top_downloaded_files(db, limit=5)
        top_files_data = []
        for item in top_files:
            if item.get("file"):  # Check if file still exists
                top_files_data.append({
                    "title": item["file"].title,
                    "downloads": item["downloads"]
                })
            else:
                # File was deleted but download record exists
                top_files_data.append({
                    "title": "[Deleted File]",
                    "downloads": item["downloads"]
                })
        
        downloads_data = await get_downloads_by_date(db, days=7)
        user_growth_data = await get_user_growth(db, days=30)
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
            "top_files": top_files_data,
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
        logger.error(f"Error in get_dashboard_stats: {e}", exc_info=True)
        # Return a more detailed error message
        error_detail = f"Error loading dashboard data: {str(e)}"
        if hasattr(e, '__cause__') and e.__cause__:
            error_detail += f" (Cause: {str(e.__cause__)})"
        raise HTTPException(status_code=500, detail=error_detail)
