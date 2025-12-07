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
    file_type: str = None,
    search: str = None,
    db: AsyncSession = Depends(get_db),
    token: dict = Depends(verify_token)
):
    """Get files list with optional filtering and search (optimized - removed Telegram API calls)"""
    from app.models.crud import get_all_files, get_files_count, search_files
    
    if search:
        files = await search_files(db, query=search, file_type=file_type, skip=skip, limit=limit)
        total = len(files)  # search_files returns limited results
    else:
        files = await get_all_files(db, file_type=file_type, skip=skip, limit=limit)
        total = await get_files_count(db, file_type=file_type)
    
    # Optimized: No Telegram API calls - much faster!
    files_data = [
        {
            "id": f.id,
            "title": f.title,
            "file_type": f.file_type,
            "downloads_count": f.downloads_count,
            "created_at": f.created_at.isoformat()
        }
        for f in files
    ]
    
    return {
        "files": files_data,
        "total": total,
        "skip": skip,
        "limit": limit,
        "search": search
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
