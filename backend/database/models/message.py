# backend/database/models/message.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey,String
from backend.database.database import Base
from datetime import datetime
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message_threads.id"))
    content = Column(String, nullable=False)
    sender = Column(Integer, ForeignKey("users.id"))
    receiver = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
