const BASE_URL = "http://localhost:8000";
let currentUser = null;
let selectedUser = null;
let selectedMessageId = null;
let socket = null;
let countdownInterval = null;

// —————••• AUTH •••—————

async function register() { /* keep your existing code (unchanged) */ }

async function verify() { /* keep your existing code (unchanged) */ }

async function resend() { /* keep your existing code (unchanged) */ }

async function login() {
  const identifier = document.getElementById("login-identifier").value.trim();
  const password = document.getElementById("login-password").value.trim();
  const responseBox = document.getElementById("response") || document.getElementById("errorMsg");

  if (!identifier || !password) {
    if (responseBox) responseBox.textContent = "⚠️ Enter both fields.";
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password })
    });
    
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch { data = { detail: text || "Empty response" }; }

    if (res.ok && data.access_token) {
      currentUser = {
        id: data.user.id,
        username: data.user.username,
        email: data.user.email,
        token: data.access_token
      };
      localStorage.setItem("chatspaceUser", JSON.stringify(currentUser));
      window.location.href = "chat.html";
    } else {
      if (responseBox) responseBox.textContent = data.detail || "Login failed";
    }
  } catch (err) {
    console.error("Login error", err);
    if (responseBox) responseBox.textContent = "🚫 Server error.";
  }
}

// —————••• CHAT INITIALIZE •••—————

function initChat() {
  const stored = localStorage.getItem("chatspaceUser");
  if (!stored) {
    return window.location.href = "login.html";
  }
  currentUser = JSON.parse(stored);
  document.getElementById("logged-user").textContent = currentUser.username;

  socket = io(BASE_URL);
  socket.emit("join", { username: currentUser.username });

  socket.on("chat_message", data => {
    if (data.to === currentUser.username) {
      appendMessage(data, false);
    }
  });

  loadUsers();
}

async function loadUsers() {
  try {
    const res = await fetch(`${BASE_URL}/chat/threads`, {
      headers: { Authorization: `Bearer ${currentUser.token}` }
    });
    const threads = await safeJSON(res);
    const userList = document.getElementById("userList");
    userList.innerHTML = "";
    threads.forEach(th => {
      const other = (th.messager1 === currentUser.username ? th.messager2 : th.messager1);
      const div = document.createElement("div");
      div.className = "user";
      div.textContent = other;
      div.onclick = () => selectUser(other, th.id, div);
      userList.appendChild(div);
    });
  } catch (err) {
    console.error("Load users error", err);
  }
}

async function selectUser(username, threadId, el) {
  selectedUser = username;
  selectedMessageId = threadId;
  document.querySelectorAll(".user").forEach(x => x.classList.remove("active"));
  el.classList.add("active");
  document.getElementById("selectedUser").textContent = username;

  try {
    const res = await fetch(`${BASE_URL}/chat/messages/${threadId}`, {
      headers: { Authorization: `Bearer ${currentUser.token}` }
    });
    const msgs = await safeJSON(res);
    const msgBox = document.getElementById("messages");
    msgBox.innerHTML = "";
    msgs.forEach(m => appendMessage(m, m.from === currentUser.username));
  } catch (err) {
    console.error("Load messages error", err);
  }
}

async function sendMessage() {
  const text = document.getElementById("messageInput").value.trim();
  if (!text || !selectedUser || !selectedMessageId) return;

  try {
    const res = await fetch(`${BASE_URL}/chat/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${currentUser.token}`
      },
      body: JSON.stringify({ to: selectedUser, message: text })
    });
    if (res.ok) {
      appendMessage({ from: currentUser.username, message: text, time: new Date().toISOString() }, true);
      document.getElementById("messageInput").value = "";
    }
  } catch (err) {
    console.error("Send message error", err);
  }
}

function appendMessage(msg, isOwn) {
  const mbox = document.getElementById("messages");
  const d = document.createElement("div");
  d.className = "message " + (isOwn ? "sent" : "received");
  d.innerHTML = `
    <div>${msg.message}</div>
    <div class="timestamp">${new Date(msg.time).toLocaleTimeString()}</div>`;
  mbox.appendChild(d);
  mbox.scrollTop = mbox.scrollHeight;
}

function logout() {
  localStorage.removeItem("chatspaceUser");
  window.location.href = "login.html";
}

// —————••• Count-down timer (verify) •••—————

function startCountdown(minutes = 10) {
  let timeLeft = minutes * 60;
  clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
    const m = Math.floor(timeLeft / 60);
    const s = timeLeft % 60;
    const timerEl = document.getElementById("timer");
    if (timerEl) timerEl.textContent = `⏳ Expires in: ${m}:${s < 10 ? "0"+s : s}`;
    timeLeft--;
    if (timeLeft < 0) {
      clearInterval(countdownInterval);
      if (timerEl) timerEl.textContent = "⏰ Code expired.";
    }
  }, 1000);
}

// —————••• Helpers •••—————

async function safeJSON(res) {
  const txt = await res.text();
  try { return JSON.parse(txt); }
  catch { return { detail: txt }; }
}
// In main.js
let peerConnection;
const config = { iceServers: [ { urls: "stun:stun.l.google.com:19302" } ] };

function startCall() {
  navigator.mediaDevices.getUserMedia({ audio: true, video: true })
    .then(stream => {
      document.getElementById("localVideo").srcObject = stream;
      setupPeerConnection();
      stream.getTracks().forEach(t => peerConnection.addTrack(t, stream));
      peerConnection.createOffer().then(o => {
        peerConnection.setLocalDescription(o);
        socket.emit("call_user", { to: targetSid, offer: o });
      });
    });
}

function setupPeerConnection() {
  peerConnection = new RTCPeerConnection(config);

  peerConnection.onicecandidate = e => {
    if (e.candidate)
      socket.emit("ice_candidate", { to: targetSid, candidate: e.candidate });
  };

  peerConnection.ontrack = e => {
    document.getElementById("remoteVideo").srcObject = e.streams[0];
  };
}

// Screenshare
function shareScreen() {
  navigator.mediaDevices.getDisplayMedia({ video: true })
    .then(stream => {
      const sender = peerConnection.getSenders().find(s => s.track.kind === 'video');
      sender.replaceTrack(stream.getVideoTracks()[0]);
      stream.getVideoTracks()[0].onended = () => {
        // revert to camera
      };
    });
}

// Socket listeners
socket.on("offer", async data => {
  targetSid = data.from;
  setupPeerConnection();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
  stream.getTracks().forEach(t => peerConnection.addTrack(t, stream));
  document.getElementById("localVideo").srcObject = stream;

  await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
  const answer = await peerConnection.createAnswer();
  await peerConnection.setLocalDescription(answer);
  socket.emit("answer_call", { to: data.from, answer });
});

socket.on("answer", data => {
  peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
});

socket.on("ice_candidate", data => {
  peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
});

// Trigger functions
document.getElementById("callBtn").onclick = startCall;
document.getElementById("screenshareBtn").onclick = shareScreen;
