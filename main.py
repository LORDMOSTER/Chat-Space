import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from socketio import ASGIApp

from backend.chat.socket_io import sio
from backend.routes.voice import router as voice_router
from backend.routes.chat import router as chat_router
from backend.auth.routes import router as auth_router
from backend.database.database import engine, Base

# ✅ Create FastAPI instance
fastapi_app = FastAPI()

# ✅ Ensure upload folder exists
os.makedirs("voice_uploads", exist_ok=True)

# ✅ Mount static directories
fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")
fastapi_app.mount("/voice/file", StaticFiles(directory="voice_uploads"), name="voice")

# ✅ Include API routers
fastapi_app.include_router(auth_router)
fastapi_app.include_router(chat_router)
fastapi_app.include_router(voice_router)

# ✅ Serve static HTML files
@fastapi_app.get("/")
def root():
    return FileResponse("static/login.html")

@fastapi_app.get("/login.html")
def login_page():
    return FileResponse("static/login.html")

@fastapi_app.get("/chat.html")
def chat_page():
    return FileResponse("static/chat.html")

@fastapi_app.get("/call.html")
def call_page():
    return FileResponse("static/call.html")

# ✅ Auto-create database tables from models
Base.metadata.create_all(bind=engine)

# ✅ Wrap FastAPI with Socket.IO server
app = ASGIApp(socketio_server=sio, other_asgi_app=fastapi_app)
