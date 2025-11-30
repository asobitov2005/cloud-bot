"""
Health check and error tracking models
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class HealthCheck(Base):
    __tablename__ = "health_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    check_type = Column(String, nullable=False, index=True)  # 'error', 'callback_error', 'failed_request'
    error_message = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)  # Exception class name
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True)  # Telegram user ID if applicable
    handler_name = Column(String, nullable=True)  # Handler/middleware name
    stack_trace = Column(Text, nullable=True)

