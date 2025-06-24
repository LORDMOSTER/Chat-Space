from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
from pytz import timezone

from backend.database.database import SessionLocal
from backend.database.models.user import User
from backend.database.models.message import Message
from backend.database.models.message_master import MessageThread
from backend.utils.jwt import get_current_user

from backend.chat.socket_io import sio,user_sid_map  # Make sure this is correct

router = APIRouter(prefix="/chat", tags=["Chat"])

# ✅ DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Get all verified users except self
@router.get("/users")
def list_all_users(request: Request, db: Session = Depends(get_db)):
    current = get_current_user(request)
    users = db.query(User).filter(User.username != current["username"], User.verified == True).all()
    return [{"username": u.username} for u in users]

# ✅ Start or return a chat thread
@router.post("/start")
def start_thread(data: dict, request: Request, db: Session = Depends(get_db)):
    user1 = get_current_user(request)["username"]
    user2 = data.get("to")

    if not user2:
        raise HTTPException(status_code=400, detail="Recipient required")

    users = sorted([user1, user2])
    thread = db.query(MessageThread).filter_by(messager1=users[0], messager2=users[1]).first()

    if not thread:
        thread = MessageThread(messager1=users[0], messager2=users[1])
        db.add(thread)
        db.commit()
        db.refresh(thread)

    return {"id": thread.id, "messager1": thread.messager1, "messager2": thread.messager2}

# ✅ Get messages in a thread
@router.get("/messages/{thread_id}")
def get_messages(thread_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)

    thread = db.query(MessageThread).filter_by(id=thread_id).first()
    if not thread or user["username"] not in [thread.messager1, thread.messager2]:
        raise HTTPException(status_code=403, detail="Unauthorized or invalid thread")

    messages = db.query(Message).filter_by(message_id=thread_id).order_by(Message.timestamp).all()
    users = {u.id: u.username for u in db.query(User).all()}

    return [
        {
            "from": users.get(msg.sender),
            "to": users.get(msg.receiver),
            "message": msg.content,
            "time": msg.timestamp.astimezone(timezone("Asia/Kolkata")).isoformat()
        }
        for msg in messages
    ]

# ✅ Send message with local time + Socket.IO emit
@router.post("/send")
def send_message(data: dict, request: Request, db: Session = Depends(get_db)):
    sender_username = get_current_user(request)["username"]
    receiver_username = data.get("to")
    message_text = data.get("message")

    if not receiver_username or not message_text:
        raise HTTPException(status_code=400, detail="Receiver and message required")

    pair = sorted([sender_username, receiver_username])
    thread = db.query(MessageThread).filter_by(messager1=pair[0], messager2=pair[1]).first()

    if not thread:
        thread = MessageThread(messager1=pair[0], messager2=pair[1])
        db.add(thread)
        db.commit()
        db.refresh(thread)

    sender = db.query(User).filter_by(username=sender_username).first()
    receiver = db.query(User).filter_by(username=receiver_username).first()

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    local_time = datetime.now(timezone("Asia/Kolkata"))

    msg = Message(
        content=message_text,
        message_id=thread.id,
        sender=sender.id,
        receiver=receiver.id,
        timestamp=local_time
    )
    db.add(msg)
    db.commit()

    # ✅ Emit message to receiver via Socket.IO
    sio.emit("chat_message", {
        "from": sender.username,
        "to": receiver.username,
        "message": message_text,
        "time": local_time.isoformat()
    }, to=receiver.username)

    return {"thread_id": thread.id, "status": "Message sent"}
@router.get("/sid/{username}")
def get_sid(username: str):
    sid = user_sid_map.get(username)
    if not sid:
        raise HTTPException(404, detail="User not connected")
    return {"sid": sid}
