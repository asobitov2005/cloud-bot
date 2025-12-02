from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, or_, and_, text, cast, Date, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from app.models.base import User, File, Download, SavedList
from app.models.settings import Settings
try:
    from app.models.health import HealthCheck
except ImportError:
    # HealthCheck model might not exist yet (migration needed)
    HealthCheck = None


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
                       blocked_only: bool = False, primary_admin_id: int = None) -> List[User]:
    """Get all users with pagination, sorted with admins first"""
    from sqlalchemy import case
    
    query = select(User)
    if blocked_only:
        query = query.where(User.is_blocked == True)
    
    # Sort: Primary admin first, then other admins, then regular users
    # Within each group, sort by joined_at descending
    if primary_admin_id:
        order_by_expr = case(
            (User.telegram_id == primary_admin_id, 0),  # Primary admin first
            (User.is_admin == True, 1),  # Other admins second
            else_=2  # Regular users last
        )
        query = query.order_by(order_by_expr, desc(User.joined_at))
    else:
        # Fallback: just sort by is_admin, then joined_at
        query = query.order_by(desc(User.is_admin), desc(User.joined_at))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def search_users(db: AsyncSession, query: str, skip: int = 0, limit: int = 50) -> List[User]:
    """Search users by username, full name, or telegram_id"""
    search_filter = or_(
        User.username.ilike(f"%{query}%"),
        User.full_name.ilike(f"%{query}%"),
        cast(User.telegram_id, String).ilike(f"%{query}%")
    )
    
    result = await db.execute(
        select(User)
        .where(search_filter)
        .offset(skip)
        .limit(limit)
        .order_by(desc(User.joined_at))
    )
    return result.scalars().all()


async def get_users_count(db: AsyncSession, query: str = None) -> int:
    """Get total users count, optionally filtered by search query"""
    stmt = select(func.count(User.id))
    
    if query:
        search_filter = or_(
            User.username.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%"),
            cast(User.telegram_id, String).ilike(f"%{query}%")
        )
        stmt = stmt.where(search_filter)
        
    result = await db.execute(stmt)
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
                              primary_admin_telegram_id: int, 
                              permissions: Optional[List[str]] = None) -> User:
    """Toggle admin status for a user
    
    Args:
        user_id: Database ID of user
        is_admin: New admin status
        primary_admin_telegram_id: Telegram ID of primary admin (cannot be demoted)
        permissions: List of permission strings (e.g., ["upload", "delete"])
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    # Protect primary admin from being demoted
    if user.telegram_id == primary_admin_telegram_id and not is_admin:
        raise ValueError("Cannot remove admin rights from primary admin")
    
    user.is_admin = is_admin
    
    # Set permissions if provided
    if permissions is not None:
        from app.models.permissions import serialize_permissions
        user.admin_permissions = serialize_permissions(permissions) if permissions else None
    elif not is_admin:
        # Clear permissions if removing admin status
        user.admin_permissions = None
    
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


async def user_has_permission(db: AsyncSession, telegram_id: int, 
                              primary_admin_id: int, permission: str) -> bool:
    """Check if user has a specific permission"""
    # Primary admin has all permissions
    if telegram_id == primary_admin_id:
        return True
    
    # Get user
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user or not user.is_admin:
        return False
    
    # If user is admin but has no permissions set, they have all permissions (backward compatibility)
    if not user.admin_permissions:
        return True
    
    # Check permissions
    from app.models.permissions import has_permission
    return has_permission(user.admin_permissions, permission)



# ==================== FILE CRUD ====================

async def update_file_processed_id(db: AsyncSession, file_id: int, processed_file_id: str) -> File:
    """Update processed_file_id for a file"""
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if file:
        file.processed_file_id = processed_file_id
        await db.commit()
        await db.refresh(file)
    return file


async def create_file(db: AsyncSession, file_id: str, title: str, 
                     file_type: str = "regular", type: str = "document",
                     level: str = None, tags: str = None,
                     description: str = None, thumbnail_id: str = None,
                     file_name: str = None, processed_file_id: str = None) -> File:
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
        file_name=file_name,
        processed_file_id=processed_file_id
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
    """
    Delete file from database
    
    Note: Downloads records are preserved (not cascade deleted) to maintain
    download statistics even after file deletion.
    """
    from sqlalchemy import delete
    
    # Check if file exists
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    
    if not file:
        return False
    
    # Delete the file using SQLAlchemy delete statement
    # This will NOT cascade delete downloads (foreign key constraint allows NULL or we keep them)
    await db.execute(delete(File).where(File.id == file_id))
    await db.commit()
    
    return True


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
    """
    Record a download
    
    Note: If there's a sequence issue (duplicate key), this will attempt to fix it
    and retry once. This can happen after migrating from SQLite to PostgreSQL.
    """
    try:
        download = Download(user_id=user_id, file_id=file_id)
        db.add(download)
        await db.commit()
        await db.refresh(download)
        return download
    except IntegrityError as e:
        # Handle sequence issues after migration
        error_str = str(e).lower()
        if "duplicate key" in error_str and "downloads_pkey" in error_str:
            # Sequence issue - try to fix it
            await db.rollback()
            try:
                from sqlalchemy import text
                # Get max ID and fix sequence
                result = await db.execute(text("SELECT COALESCE(MAX(id), 0) FROM downloads"))
                max_id = result.scalar() or 0
                await db.execute(text(f"SELECT setval('downloads_id_seq', {max_id + 1}, false)"))
                await db.commit()
                
                # Retry the insert
                download = Download(user_id=user_id, file_id=file_id)
                db.add(download)
                await db.commit()
                await db.refresh(download)
                return download
            except Exception as fix_error:
                await db.rollback()
                # If fixing fails, just log and re-raise
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Could not fix downloads sequence: {fix_error}")
                raise
        else:
            # Other integrity errors - re-raise
            await db.rollback()
            raise


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
    """
    Get top downloaded files
    
    Note: Only returns files that still exist (not deleted).
    Download records for deleted files are preserved but not shown here.
    """
    query = select(File).where(File.id.isnot(None)).order_by(desc(File.downloads_count)).limit(limit)
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
    """Get user growth over the last N days, filling in missing dates with 0"""
    from datetime import date as date_type
    
    start_date = datetime.utcnow() - timedelta(days=days)
    query = select(
        func.date(User.joined_at).label('date'),
        func.count(User.id).label('count')
    ).where(User.joined_at >= start_date)\
     .group_by(func.date(User.joined_at))\
     .order_by('date')
    
    result = await db.execute(query)
    data_dict = {str(row.date): row.count for row in result}
    
    # Fill in missing dates with 0
    filled_data = []
    for i in range(days):
        current_date = (datetime.utcnow() - timedelta(days=days - 1 - i)).date()
        date_str = str(current_date)
        count = data_dict.get(date_str, 0)
        # Format date for display (e.g., "2024-01-15" -> "Jan 15")
        formatted_date = current_date.strftime("%b %d")
        filled_data.append({"date": formatted_date, "count": count})
    
    return filled_data


async def get_users_by_country(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get user distribution by country (using language as proxy)"""
    query = select(
        User.language,
        func.count(User.id).label('count')
    ).group_by(User.language)\
     .order_by(desc('count'))
    
    result = await db.execute(query)
    return [{"country": row.language, "count": row.count} for row in result]


async def get_users_by_gender(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get user distribution by gender"""
    try:
        query = select(
            User.gender,
            func.count(User.id).label('count')
        ).group_by(User.gender)\
         .order_by(desc('count'))
        
        result = await db.execute(query)
        gender_data = [{"gender": row.gender or "Unknown", "count": row.count} for row in result]
        
        # Filter out "Unknown" if it's the only category or if all users are Unknown
        # Since Telegram doesn't provide gender, we'll only show if there's actual gender data
        if len(gender_data) == 1 and gender_data[0]["gender"] == "Unknown":
            # All users are Unknown, return empty to hide the chart
            return []
        
        # Filter out Unknown entries if there are other categories
        return [item for item in gender_data if item["gender"] != "Unknown"]
    except Exception:
        # Gender column doesn't exist yet, return empty data
        return []


async def get_users_joined_stats(db: AsyncSession) -> Dict[str, int]:
    """Get users joined: today, this week, this month"""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1)
    
    # Today
    today_query = select(func.count(User.id)).where(
        User.joined_at >= today_start
    )
    today_result = await db.execute(today_query)
    today_count = today_result.scalar() or 0
    
    # This week
    week_query = select(func.count(User.id)).where(
        User.joined_at >= week_start
    )
    week_result = await db.execute(week_query)
    week_count = week_result.scalar() or 0
    
    # This month
    month_query = select(func.count(User.id)).where(
        User.joined_at >= month_start
    )
    month_result = await db.execute(month_query)
    month_count = month_result.scalar() or 0
    
    return {
        "today": today_count,
        "week": week_count,
        "month": month_count
    }


async def get_users_left_stats(db: AsyncSession) -> Dict[str, int]:
    """Get users left: today, this week, this month (blocked users)"""
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1)
    
    # Note: We track blocked users, but we don't have a "left_at" timestamp
    # So we'll use blocked users as a proxy for users who left
    # For more accurate tracking, we'd need to add a "left_at" field
    
    # Today (blocked today - approximate)
    today_query = select(func.count(User.id)).where(
        User.is_blocked == True,
        User.joined_at >= today_start  # Approximate: users who joined and were blocked today
    )
    today_result = await db.execute(today_query)
    today_count = today_result.scalar() or 0
    
    # This week
    week_query = select(func.count(User.id)).where(
        User.is_blocked == True,
        User.joined_at >= week_start
    )
    week_result = await db.execute(week_query)
    week_count = week_result.scalar() or 0
    
    # This month
    month_query = select(func.count(User.id)).where(
        User.is_blocked == True,
        User.joined_at >= month_start
    )
    month_result = await db.execute(month_query)
    month_count = month_result.scalar() or 0
    
    return {
        "today": today_count,
        "week": week_count,
        "month": month_count
    }


async def get_total_files_volume(db: AsyncSession) -> Dict[str, Any]:
    """Get total files volume in bytes"""
    try:
        from app.bot.main import _bot_instance
        if not _bot_instance:
            return {"total_bytes": 0, "formatted": "0 B"}
        
        # Get all files
        files_query = select(File)
        files_result = await db.execute(files_query)
        files = files_result.scalars().all()
        
        total_bytes = 0
        for file in files:
            try:
                file_info = await _bot_instance.get_file(file.file_id)
                if file_info and file_info.file_size:
                    total_bytes += file_info.file_size
            except Exception:
                # Skip files we can't get info for
                continue
        
        # Format bytes
        from app.bot.helpers import format_file_size
        return {
            "total_bytes": total_bytes,
            "formatted": format_file_size(total_bytes)
        }
    except Exception:
        return {"total_bytes": 0, "formatted": "0 B"}


async def get_downloads_by_period(db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    """Get downloads grouped by daily, weekly, and monthly"""
    from app.core.database import get_database_url
    from sqlalchemy import text
    
    db_url = get_database_url()
    is_postgresql = db_url.startswith("postgresql")
    
    now = datetime.utcnow()
    
    # Daily (last 30 days)
    daily_start = now - timedelta(days=30)
    if is_postgresql:
        # PostgreSQL: use cast to DATE
        daily_query = select(
            cast(Download.downloaded_at, Date).label('date'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= daily_start)\
         .group_by(cast(Download.downloaded_at, Date))\
         .order_by(cast(Download.downloaded_at, Date))
    else:
        # SQLite
        daily_query = select(
            func.date(Download.downloaded_at).label('date'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= daily_start)\
         .group_by(func.date(Download.downloaded_at))\
         .order_by('date')
    daily_result = await db.execute(daily_query)
    daily_data = [{"date": str(row.date), "count": row.count} for row in daily_result]
    
    # Weekly (last 12 weeks)
    weekly_start = now - timedelta(weeks=12)
    if is_postgresql:
        # PostgreSQL: use DATE_TRUNC('week', ...) to get start of week (Monday)
        # Create the expression once and reuse it
        week_trunc = cast(func.date_trunc('week', Download.downloaded_at), Date)
        weekly_query = select(
            week_trunc.label('week_start'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= weekly_start)\
         .group_by(week_trunc)\
         .order_by(week_trunc)
    else:
        # SQLite: use date arithmetic
        weekly_query = select(
            func.date(Download.downloaded_at, 'weekday 0', '-6 days').label('week_start'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= weekly_start)\
         .group_by(func.date(Download.downloaded_at, 'weekday 0', '-6 days'))\
         .order_by('week_start')
    weekly_result = await db.execute(weekly_query)
    weekly_data = [{"period": str(row.week_start), "count": row.count} for row in weekly_result]
    
    # Monthly (last 12 months)
    monthly_start = now - timedelta(days=365)
    if is_postgresql:
        # PostgreSQL: use TO_CHAR function
        # Create the expression once and reuse it
        month_char = func.to_char(Download.downloaded_at, text("'YYYY-MM'"))
        monthly_query = select(
            month_char.label('month'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= monthly_start)\
         .group_by(month_char)\
         .order_by(month_char)
    else:
        # SQLite: use strftime
        monthly_query = select(
            func.strftime('%Y-%m', Download.downloaded_at).label('month'),
            func.count(Download.id).label('count')
        ).where(Download.downloaded_at >= monthly_start)\
         .group_by(func.strftime('%Y-%m', Download.downloaded_at))\
         .order_by('month')
    monthly_result = await db.execute(monthly_query)
    monthly_data = [{"period": row.month, "count": row.count} for row in monthly_result]
    
    return {
        "daily": daily_data,
        "weekly": weekly_data,
        "monthly": monthly_data
    }


async def log_health_check(db: AsyncSession, check_type: str, error_message: str = None,
                           error_type: str = None, user_id: int = None,
                           handler_name: str = None, stack_trace: str = None):
    """Log a health check event (error, callback error, failed request)"""
    health_check = HealthCheck(
        check_type=check_type,
        error_message=error_message,
        error_type=error_type,
        user_id=user_id,
        handler_name=handler_name,
        stack_trace=stack_trace
    )
    db.add(health_check)
    await db.commit()
    await db.refresh(health_check)
    return health_check


async def get_health_stats(db: AsyncSession, days: int = 7) -> Dict[str, Any]:
    """
    Get health check statistics
    
    Returns empty stats if health_checks table doesn't exist (graceful degradation)
    """
    # Check if HealthCheck model is available
    if HealthCheck is None:
        return {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_day": []
        }
    
    try:
        from app.core.database import get_database_url
        from sqlalchemy import cast, Date
        
        db_url = get_database_url()
        is_postgresql = db_url.startswith("postgresql")
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total errors by type
        errors_query = select(
            HealthCheck.check_type,
            func.count(HealthCheck.id).label('count')
        ).where(HealthCheck.occurred_at >= start_date)\
         .group_by(HealthCheck.check_type)
        errors_result = await db.execute(errors_query)
        errors_by_type = {row.check_type: row.count for row in errors_result}
        
        # Errors by day
        if is_postgresql:
            # PostgreSQL: use cast to DATE
            errors_by_day_query = select(
                cast(HealthCheck.occurred_at, Date).label('date'),
                func.count(HealthCheck.id).label('count')
            ).where(HealthCheck.occurred_at >= start_date)\
             .group_by(cast(HealthCheck.occurred_at, Date))\
             .order_by(cast(HealthCheck.occurred_at, Date))
        else:
            # SQLite
            errors_by_day_query = select(
                func.date(HealthCheck.occurred_at).label('date'),
                func.count(HealthCheck.id).label('count')
            ).where(HealthCheck.occurred_at >= start_date)\
             .group_by(func.date(HealthCheck.occurred_at))\
             .order_by('date')
        errors_by_day_result = await db.execute(errors_by_day_query)
        errors_by_day = [{"date": str(row.date), "count": row.count} for row in errors_by_day_result]
        
        # Total errors
        total_errors_query = select(func.count(HealthCheck.id)).where(
            HealthCheck.occurred_at >= start_date
        )
        total_errors_result = await db.execute(total_errors_query)
        total_errors = total_errors_result.scalar() or 0
        
        return {
            "total_errors": total_errors,
            "errors_by_type": errors_by_type,
            "errors_by_day": errors_by_day
        }
    except Exception as e:
        # If table doesn't exist or any other error, return empty stats
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not get health stats (table may not exist): {e}")
        return {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_day": []
        }


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


# ==================== FORCE SUBSCRIBE (FSUB) CRUD ====================

async def get_force_subscribe_channels(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get all force subscribe channels"""
    import json
    channels_json = await get_setting(db, "force_subscribe_channels")
    if not channels_json:
        return []
    try:
        return json.loads(channels_json)
    except (json.JSONDecodeError, TypeError):
        return []


async def add_force_subscribe_channel(db: AsyncSession, channel_id: int, 
                                      channel_username: str = None, 
                                      channel_title: str = None,
                                      invite_link: str = None) -> bool:
    """Add a force subscribe channel"""
    import json
    channels = await get_force_subscribe_channels(db)
    
    # Check if channel already exists
    for channel in channels:
        if channel.get("channel_id") == channel_id:
            return False  # Already exists
    
    # Add new channel
    channels.append({
        "channel_id": channel_id,
        "channel_username": channel_username,
        "channel_title": channel_title,
        "invite_link": invite_link
    })
    
    await set_setting(db, "force_subscribe_channels", json.dumps(channels))
    return True


async def remove_force_subscribe_channel(db: AsyncSession, channel_id: int) -> bool:
    """Remove a force subscribe channel"""
    import json
    channels = await get_force_subscribe_channels(db)
    
    # Filter out the channel
    original_count = len(channels)
    channels = [ch for ch in channels if ch.get("channel_id") != channel_id]
    
    if len(channels) == original_count:
        return False  # Channel not found
    
    # Update settings
    if channels:
        await set_setting(db, "force_subscribe_channels", json.dumps(channels))
    else:
        await delete_setting(db, "force_subscribe_channels")
    
    return True
