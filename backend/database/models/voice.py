# backend/database/models/voice.py

from sqlalchemy import Column, Integer, String, DateTime
from backend.database.database import Base

class Voice(Base):
    __tablename__ = "voice_uploads"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
