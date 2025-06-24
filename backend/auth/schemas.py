from pydantic import BaseModel, EmailStr

class RegisterInput(BaseModel):
    username: str
    email: EmailStr
    password: str

class VerifyInput(BaseModel):
    email: EmailStr
    code: str

class ResendInput(BaseModel):
    email: EmailStr

class LoginInput(BaseModel):
    identifier: str
    password: str
