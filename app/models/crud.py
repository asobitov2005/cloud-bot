from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.models.base import User, File, Download, SavedList
from app.models.settings import Settings


# ==================== USER CRUD ====================

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, telegram_id: int, username: str = None, 
                     full_name: str = None, language: str = "uz") -> User:
    """Create new user"""
    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        language=language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_language(db: AsyncSession, user_id: int, language: str) -> User:
    """Update user language preference"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.language = language
    await db.commit()
    await db.refresh(user)
    return user


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 50, 
                       blocked_only: bool = False) -> List[User]:
    """Get all users with pagination"""
    query = select(User)
    if blocked_only:
        query = query.where(User.is_blocked == True)
    query = query.offset(skip).limit(limit).order_by(desc(User.joined_at))
    result = await db.execute(query)
    return result.scalars().all()


async def get_users_count(db: AsyncSession) -> int:
    """Get total users count"""
    result = await db.execute(select(func.count(User.id)))
    return result.scalar()


async def block_user(db: AsyncSession, user_id: int) -> User:
    """Block user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_blocked = True
    await db.commit()
    await db.refresh(user)
    return user


async def unblock_user(db: AsyncSession, user_id: int) -> User:
    """Unblock user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.is_blocked = False
    await db.commit()
    await db.refresh(user)
    return user


async def toggle_admin_status(db: AsyncSession, user_id: int, is_admin: bool, 
                              primary_admin_telegram_id: int) -> User:
    """Toggle admin status for a user
    
    Args:
        user_id: Database ID of user
        is_admin: New admin status
        primary_admin_telegram_id: Telegram ID of primary admin (cannot be demoted)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    # Protect primary admin from being demoted
    if user.telegram_id == primary_admin_telegram_id and not is_admin:
        raise ValueError("Cannot remove admin rights from primary admin")
    
    user.is_admin = is_admin
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by database ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def is_user_admin(db: AsyncSession, telegram_id: int, 
                       primary_admin_id: int) -> bool:
    """Check if user is admin by Telegram ID"""
    # Check if user is primary admin
    if telegram_id == primary_admin_id:
        return True
    
    # Check if user has admin status in database
    user = await get_user_by_telegram_id(db, telegram_id)
    if user and user.is_admin:
        return True
    
    return False



# ==================== FILE CRUD ====================

async def create_file(db: AsyncSession, file_id: str, title: str, 
                      file_type: str = "regular", type: str = "document",
                      level: str = None, tags: str = None, 
                      description: str = None, thumbnail_id: str = None,
                      file_name: str = None) -> File:
    """Create new file"""
    db_file = File(
        file_id=file_id,
        title=title,
        file_type=file_type,
        type=type,
        level=level,
        tags=tags,
        description=description,
        thumbnail_id=thumbnail_id,
        file_name=file_name
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file


async def get_file_by_id(db: AsyncSession, file_id: int) -> Optional[File]:
    """Get file by ID"""
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()


async def get_file_by_telegram_file_id(db: AsyncSession, telegram_file_id: str) -> Optional[File]:
    """Get file by Telegram file_id"""
    result = await db.execute(select(File).where(File.file_id == telegram_file_id))
    return result.scalar_one_or_none()


async def search_files(db: AsyncSession, query: str, file_type: str = None,
                      skip: int = 0, limit: int = 5) -> List[File]:
    """Search files by title (case-insensitive)"""
    conditions = [File.title.ilike(f"%{query}%")]
    
    if file_type:
        conditions.append(File.file_type == file_type)
        
    search_query = select(File).where(and_(*conditions))\
        .offset(skip).limit(limit).order_by(desc(File.created_at))
    
    result = await db.execute(search_query)
    return result.scalars().all()


async def get_all_files(db: AsyncSession, file_type: str = None,
                       skip: int = 0, limit: int = 50) -> List[File]:
    """Get all files with pagination"""
    query = select(File)
    
    if file_type:
        query = query.where(File.file_type == file_type)
        
    query = query.offset(skip).limit(limit).order_by(desc(File.created_at))
    result = await db.execute(query)
    return result.scalars().all()


async def get_files_count(db: AsyncSession, file_type: str = None) -> int:
    """Get total files count"""
    query = select(func.count(File.id))
    if file_type:
        query = query.where(File.file_type == file_type)
    result = await db.execute(query)
    return result.scalar()


async def delete_file(db: AsyncSession, file_id: int) -> bool:
    """Delete file"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file:
        await db.delete(file)
        await db.commit()
        return True
    return False


async def update_file(db: AsyncSession, file_id: int, **kwargs) -> Optional[File]:
    """Update file metadata"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file:
        for key, value in kwargs.items():
            if hasattr(file, key):
                setattr(file, key, value)
        await db.commit()
        await db.refresh(file)
    return file


async def increment_download_count(db: AsyncSession, file_id: int) -> None:
    """Increment file download count"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file:
        file.downloads_count += 1
        await db.commit()


# ==================== DOWNLOAD CRUD ====================

async def create_download(db: AsyncSession, user_id: int, file_id: int) -> Download:
    """Record a download"""
    download = Download(user_id=user_id, file_id=file_id)
    db.add(download)
    await db.commit()
    await db.refresh(download)
    return download


async def get_user_downloads(db: AsyncSession, user_id: int, 
                            skip: int = 0, limit: int = 50) -> List[Download]:
    """Get user's download history"""
    query = select(Download).where(Download.user_id == user_id)\
        .options(selectinload(Download.file))\
        .offset(skip).limit(limit).order_by(desc(Download.downloaded_at))
    result = await db.execute(query)
    return result.scalars().all()


async def get_total_downloads(db: AsyncSession) -> int:
    """Get total downloads count"""
    result = await db.execute(select(func.count(Download.id)))
    return result.scalar()


async def get_top_downloaded_files(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top downloaded files"""
    query = select(File).order_by(desc(File.downloads_count)).limit(limit)
    result = await db.execute(query)
    files = result.scalars().all()
    return [{"file": file, "downloads": file.downloads_count} for file in files]


# ==================== SAVED LIST CRUD ====================

async def add_to_saved_list(db: AsyncSession, user_id: int, file_id: int) -> Optional[SavedList]:
    """Add file to user's saved list"""
    # Check if already saved
    existing = await db.execute(
        select(SavedList).where(
            and_(SavedList.user_id == user_id, SavedList.file_id == file_id)
        )
    )
    if existing.scalar_one_or_none():
        return None  # Already saved
    
    saved = SavedList(user_id=user_id, file_id=file_id)
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return saved


async def remove_from_saved_list(db: AsyncSession, user_id: int, file_id: int) -> bool:
    """Remove file from user's saved list"""
    result = await db.execute(
        select(SavedList).where(
            and_(SavedList.user_id == user_id, SavedList.file_id == file_id)
        )
    )
    saved = result.scalar_one_or_none()
    if saved:
        await db.delete(saved)
        await db.commit()
        return True
    return False


from sqlalchemy.orm import selectinload

async def get_user_saved_files(db: AsyncSession, user_id: int,
                               skip: int = 0, limit: int = 50) -> List[SavedList]:
    """Get user's saved files"""
    query = select(SavedList).where(SavedList.user_id == user_id)\
        .options(selectinload(SavedList.file))\
        .offset(skip).limit(limit).order_by(desc(SavedList.saved_at))
    result = await db.execute(query)
    return result.scalars().all()


async def is_file_saved(db: AsyncSession, user_id: int, file_id: int) -> bool:
    """Check if file is in user's saved list"""
    result = await db.execute(
        select(SavedList).where(
            and_(SavedList.user_id == user_id, SavedList.file_id == file_id)
        )
    )
    return result.scalar_one_or_none() is not None


# ==================== ANALYTICS ====================

async def get_downloads_by_date(db: AsyncSession, days: int = 7) -> List[Dict[str, Any]]:
    """Get downloads grouped by date for the last N days"""
    start_date = datetime.utcnow() - timedelta(days=days)
    query = select(
        func.date(Download.downloaded_at).label('date'),
        func.count(Download.id).label('count')
    ).where(Download.downloaded_at >= start_date)\
     .group_by(func.date(Download.downloaded_at))\
     .order_by('date')
    
    result = await db.execute(query)
    return [{"date": str(row.date), "count": row.count} for row in result]


async def get_user_growth(db: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
    """Get user growth over the last N days"""
    start_date = datetime.utcnow() - timedelta(days=days)
    query = select(
        func.date(User.joined_at).label('date'),
        func.count(User.id).label('count')
    ).where(User.joined_at >= start_date)\
     .group_by(func.date(User.joined_at))\
     .order_by('date')
    
    result = await db.execute(query)
    return [{"date": str(row.date), "count": row.count} for row in result]


# ==================== SETTINGS CRUD ====================

async def get_setting(db: AsyncSession, key: str) -> Optional[str]:
    """Get setting value by key"""
    result = await db.execute(select(Settings).where(Settings.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str) -> Settings:
    """Set setting value"""
    result = await db.execute(select(Settings).where(Settings.key == key))
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    return setting


async def delete_setting(db: AsyncSession, key: str) -> bool:
    """Delete setting"""
    result = await db.execute(select(Settings).where(Settings.key == key))
    setting = result.scalar_one_or_none()
    
    if setting:
        await db.delete(setting)
        await db.commit()
        return True
    return False
