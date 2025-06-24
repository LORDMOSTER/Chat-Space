# backend/database/models/message_master.py

from sqlalchemy import Column, Integer, String
from backend.database.database import Base

class MessageThread(Base):
    __tablename__ = "message_threads"

    id = Column(Integer, primary_key=True, index=True)
    messager1 = Column(String(50), nullable=False)
    messager2 = Column(String(50), nullable=False)
