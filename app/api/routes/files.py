from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.crud import (
    get_all_files, get_file_by_id, search_files, delete_file, update_file,
    get_files_count
)
from app.api.auth import verify_token, verify_web_token


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request, auth_result = Depends(verify_web_token)):
    """Files management page"""
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("files.html", {"request": request})


@router.get("/api/files")
async def get_files(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    file_type: str = None,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get files list with file sizes"""
    # Get total count for pagination
    total_count = await get_files_count(db, file_type=file_type)
    
    if search:
        files = await search_files(db, search, file_type=file_type, skip=skip, limit=limit)
    else:
        files = await get_all_files(db, file_type=file_type, skip=skip, limit=limit)
    
    # Get file sizes from Telegram
    from app.bot.main import _bot_instance
    from app.bot.helpers import format_file_size
    
    files_data = []
    for f in files:
        file_size_bytes = 0
        file_size_formatted = "0 B"
        
        if _bot_instance:
            try:
                file_info = await _bot_instance.get_file(f.file_id)
                if file_info and file_info.file_size:
                    file_size_bytes = file_info.file_size
                    file_size_formatted = format_file_size(file_size_bytes)
            except Exception:
                pass  # Keep default 0 if we can't get file size
        
        files_data.append({
            "id": f.id,
            "title": f.title,
            "level": f.level,
            "tags": f.tags,
            "file_type": f.file_type,
            "file_size_bytes": file_size_bytes,
            "file_size_formatted": file_size_formatted,
            "downloads_count": f.downloads_count,
            "created_at": f.created_at.isoformat()
        })
    
    return {
        "files": files_data,
        "total": total_count,
        "skip": skip,
        "limit": limit
    }


@router.get("/api/files/{file_id}")
async def get_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get file details"""
    file = await get_file_by_id(db, file_id)
    if not file:
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    return {
        "id": file.id,
        "title": file.title,
        "level": file.level,
        "tags": file.tags,
        "description": file.description,
        "file_type": file.file_type,
        "downloads_count": file.downloads_count,
        "created_at": file.created_at.isoformat()
    }


@router.put("/api/files/{file_id}")
async def update_file_metadata(
    file_id: int,
    title: str = Form(...),
    level: str = Form(None),
    tags: str = Form(None),
    description: str = Form(None),
    file_type: str = Form("regular"),
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Update file metadata"""
    file = await update_file(
        db,
        file_id,
        title=title,
        level=level,
        tags=tags,
        description=description,
        file_type=file_type
    )
    
    if not file:
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    return {"success": True, "message": "File updated successfully"}


@router.delete("/api/files/{file_id}")
async def delete_file_route(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Delete file"""
    deleted = await delete_file(db, file_id)
    
    if not deleted:
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    return {"success": True, "message": "File deleted successfully"}
