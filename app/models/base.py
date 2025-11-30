from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

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
    created_at = Column(DateTime, default=datetime.utcnow)
    downloads_count = Column(Integer, default=0)

    downloads = relationship("Download", back_populates="file")
    saved_in = relationship("SavedList", back_populates="file")

class Download(Base):
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_id = Column(Integer, ForeignKey("files.id"))
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
