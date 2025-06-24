# backend/database/models/verification.py

from sqlalchemy import Column, String, DateTime
from backend.database.database import Base

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    email = Column(String(100), primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(200), nullable=False)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
