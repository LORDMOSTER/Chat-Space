# backend/utils/jwt.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Request, HTTPException

# Secret key used to sign the JWTs (Use env var in production)
SECRET_KEY = "MWW7h_yyBtlgR7QBcTldgPiYKhsZrYb4xdJ4w_hY1KdQZVvwVRe_zUZWUlMahZsAmqd8E7DnyqP_7puF4W4ISg"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 🔐 Create JWT Token with explicit 'sub'
def create_access_token(data: dict):
    if "sub" not in data:
        raise HTTPException(status_code=400, detail="Token payload must include 'sub'")
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

# ✅ Decode and return current user from token
def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = token.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalid: 'sub' missing")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token decoding failed")
