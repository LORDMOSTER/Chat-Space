import socketio

# 🔌 Create Async Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi')

# 🌐 ASGI App (used in main.py)
user_sid_map = {}  # {username: sid}

# ✅ Handle user joining
@sio.event
async def join(sid, data):
    username = data.get("username")
    if username:
        user_sid_map[username] = sid
        await sio.save_session(sid, {"username": username})
        await sio.enter_room(sid, username)
        print(f"✅ {username} joined with SID: {sid}")

# 🔌 Handle disconnect
@sio.event
async def disconnect(sid):
    print(f"❌ Disconnected: {sid}")
    for username, saved_sid in list(user_sid_map.items()):
        if saved_sid == sid:
            print(f"👋 {username} disconnected")
            user_sid_map.pop(username, None)
            break

# 📨 Handle incoming chat messages
@sio.event
async def send_message(sid, data):
    from_user = data.get("from")
    to_user = data.get("to")
    message = data.get("message")
    time = data.get("time")
    if from_user and to_user and message:
        print(f"📨 {from_user} ➡️ {to_user}: {message}")
        await sio.emit("chat_message", {
            "from": from_user,
            "to": to_user,
            "message": message,
            "time": time
        }, room=to_user)

# 📞 Call invitation
@sio.event
async def start_call(sid, data):
    # data = { "from": "caller", "to": "target" }
    target_sid = user_sid_map.get(data.get("to"))
    if target_sid:
        await sio.emit("incoming_call", {
            "from": data.get("from")
        }, to=target_sid)
        print(f"📞 Call initiated from {data.get('from')} to {data.get('to')}")

# 🔁 Get SID of user (if needed for direct routing)
@sio.event
async def get_sid(sid, data):
    target = data.get("for")
    await sio.emit("user_sid", {
        "username": target,
        "sid": user_sid_map.get(target)
    }, to=sid)

# 🔁 WebRTC: offer from caller
@sio.on('call_user')
async def call_user(sid, data):
    # { to: target_username, offer }
    target_sid = user_sid_map.get(data['to'])
    if target_sid:
        await sio.emit('offer', {
            "from": data['from'],
            "offer": data['offer']
        }, to=target_sid)

# 🔁 WebRTC: answer from callee
@sio.on('answer_call')
async def answer_call(sid, data):
    # { to: caller_username, answer }
    target_sid = user_sid_map.get(data['to'])
    if target_sid:
        await sio.emit('answer', {
            "from": data['from'],
            "answer": data['answer']
        }, to=target_sid)

# 🔁 WebRTC: ICE candidate
@sio.on('ice_candidate')
async def ice_candidate(sid, data):
    # { to: other_username, candidate }
    target_sid = user_sid_map.get(data['to'])
    if target_sid:
        await sio.emit('ice_candidate', {
            "from": data['from'],
            "candidate": data['candidate']
        }, to=target_sid)
