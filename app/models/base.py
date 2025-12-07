from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# Import models to ensure they're registered with Base
try:
    from app.models.health import HealthCheck
except ImportError:
    HealthCheck = None


# Admin Role Enum
class AdminRole(str, enum.Enum):
    """Admin role types"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


# ==================== ADMIN MODELS ====================

class AdminUser(Base):
    """Separate admin user table for dashboard access"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    role = Column(Enum(AdminRole), nullable=False, default=AdminRole.ADMIN)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    logs = relationship("AdminLog", back_populates="admin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AdminUser {self.username} ({self.role})>"


class AdminLog(Base):
    """Audit log for all admin actions"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    action_type = Column(String, nullable=False, index=True)  # login, create, update, delete, etc.
    target_type = Column(String, nullable=True)  # user, file, admin, settings, etc.
    target_id = Column(String, nullable=True)  # ID of the affected resource
    details = Column(Text, nullable=True)  # JSON with additional info
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    admin = relationship("AdminUser", back_populates="logs")

    def __repr__(self):
        return f"<AdminLog {self.action_type} by admin_id={self.admin_id}>"


# ==================== BOT USER MODELS ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    language = Column(String, default="uz")
    gender = Column(String, nullable=True)  # 'male', 'female', 'other', or None
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)
    blocked_at = Column(DateTime, nullable=True)  # Track when user was blocked
    is_admin = Column(Boolean, default=False, index=True)
    admin_permissions = Column(Text, nullable=True)  # JSON string of permissions

    downloads = relationship("Download", back_populates="user")
    saved_files = relationship("SavedList", back_populates="user")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, nullable=False)  # Telegram file_id
    file_name = Column(String, nullable=True) # Original filename
    title = Column(String, index=True, nullable=False)
    type = Column(String, default="document") # document, audio, etc.
    file_type = Column(String, default="regular", index=True) # regular or mock_test
    level = Column(String, nullable=True, index=True)
    tags = Column(String, nullable=True) # Comma separated tags
    description = Column(Text, nullable=True)
    thumbnail_id = Column(String, nullable=True) # Telegram file_id for thumbnail
    processed_file_id = Column(String, nullable=True) # Pre-processed file with thumbnail and renamed
    file_size = Column(BigInteger, nullable=True)  # File size in bytes
    created_at = Column(DateTime, default=datetime.utcnow)
    downloads_count = Column(Integer, default=0)

    downloads = relationship("Download", back_populates="file")
    saved_in = relationship("SavedList", back_populates="file")

class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_id = Column(Integer, ForeignKey("files.id", ondelete="SET NULL"))  # Keep download records even if file is deleted
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="downloads")
    file = relationship("File", back_populates="downloads")

class SavedList(Base):
    __tablename__ = "saved_list"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_id = Column(Integer, ForeignKey("files.id"))
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_files")
    file = relationship("File", back_populates="saved_in")
