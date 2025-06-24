from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
import random, string

from backend.utils.jwt import create_access_token, get_current_user
from backend.database.database import SessionLocal
from backend.database.models.user import User
from backend.database.models.verification import VerificationCode
from backend.database.models.login_history import LoginHistory
from backend.utils.hashing import hash_password
from backend.utils.email_utils import send_verification_email
from passlib.context import CryptContext
from backend.auth.schemas import RegisterInput, LoginInput, VerifyInput, ResendInput

router = APIRouter(tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Register
@router.post("/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, detail="📧 Email already exists")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, detail="👤 Username already exists")

    db.query(VerificationCode).filter_by(email=data.email).delete()

    code = ''.join(random.choices(string.digits, k=6))
    hashed_password = hash_password(data.password)

    verification = VerificationCode(
        email=data.email,
        username=data.username,
        password=hashed_password,
        code=code,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )

    db.add(verification)
    db.commit()
    send_verification_email(data.email, code)

    return {"message": "📩 Verification code sent to your email"}

# ✅ Verify Email
@router.post("/verify")
def verify(data: VerifyInput, db: Session = Depends(get_db)):
    record = db.query(VerificationCode).filter_by(email=data.email).first()

    if not record:
        raise HTTPException(404, detail="No verification request found")
    if datetime.utcnow() > record.expires_at:
        raise HTTPException(400, detail="⏰ Code expired")
    if record.code != data.code:
        raise HTTPException(401, detail="❌ Invalid code")

    user = User(
        username=record.username,
        email=record.email,
        password=record.password,
        verified=True
    )

    db.add(user)
    db.delete(record)
    db.commit()

    return {"message": "✅ Email verified. User account created."}

# 🔁 Resend Verification Code
@router.post("/resend")
def resend(data: ResendInput, db: Session = Depends(get_db)):
    record = db.query(VerificationCode).filter_by(email=data.email).first()

    if not record:
        raise HTTPException(404, detail="No verification found. Please register again.")

    code = ''.join(random.choices(string.digits, k=6))
    record.code = code
    record.created_at = datetime.utcnow()
    record.expires_at = datetime.utcnow() + timedelta(minutes=10)

    db.commit()
    send_verification_email(data.email, code)

    return {"message": "🔁 New verification code sent"}

# 🔐 Login
@router.post("/login")
def login(request: Request, data: dict, db: Session = Depends(get_db)):
    print("🔑 Token login route hit")
    identifier = data.get("identifier")
    password = data.get("password")
    
    if not identifier or not password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    user = db.query(User).filter(
        or_(User.username == identifier, User.email == identifier)
    ).first()

    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    # ✅ Generate JWT token
    token = create_access_token({"sub": user.username})
    print("Generated Token:", token)

    return {
        "message": "✅ Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        },
        "access_token": token,
        "token_type": "bearer"
    }
