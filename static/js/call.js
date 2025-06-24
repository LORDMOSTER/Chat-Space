const socket = io("http://localhost:8000");
let pc, localStream, remoteStream;
const peer = new URLSearchParams(window.location.search).get('peer');
document.getElementById('peerName').textContent = peer;
socket.emit('join', { username: localStorage.getItem('chatspaceUser') ? JSON.parse(localStorage.getItem('chatspaceUser')).username : '' });

async function initMedia() {
  localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
  document.getElementById('localVideo').srcObject = localStream;
}

function createPeer() {
  pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
  localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
  remoteStream = new MediaStream();
  document.getElementById('remoteVideo').srcObject = remoteStream;
  pc.ontrack = e => e.streams[0].getTracks().forEach(t => remoteStream.addTrack(t));
  pc.onicecandidate = e => {
    if (e.candidate) {
      socket.emit('ice_candidate', { to: peer, candidate: e.candidate });
    }
  };
}

socket.on('offer', async data => {
  if (data.from !== peer) return;
  await initMedia();
  createPeer();
  await pc.setRemoteDescription(data.offer);
  const ans = await pc.createAnswer();
  await pc.setLocalDescription(ans);
  socket.emit('answer_call', { to: data.from, answer: ans });
});

socket.on('answer', data => {
  if (data.from !== peer) return;
  pc.setRemoteDescription(data.answer);
});

socket.on('ice_candidate', data => {
  if (data.from !== peer) return;
  pc.addIceCandidate(data.candidate);
});

async function startCall() {
  await initMedia();
  createPeer();
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  socket.emit('call_user', { to: peer, offer });
}

// Button controls:
document.getElementById('btnToggleMic').onclick = () => {
  const track = localStream.getAudioTracks()[0];
  track.enabled = !track.enabled;
  event.target.textContent = track.enabled ? '🎤 On' : '🎤 Off';
};
document.getElementById('btnToggleVideo').onclick = () => {
  const track = localStream.getVideoTracks()[0];
  track.enabled = !track.enabled;
  event.target.textContent = track.enabled ? '🎥 On' : '🎥 Off';
};
document.getElementById('btnShareScreen').onclick = async () => {
  const screen = await navigator.mediaDevices.getDisplayMedia({ video: true });
  const sender = pc.getSenders().find(s => s.track.kind === 'video');
  sender.replaceTrack(screen.getVideoTracks()[0]);
};
document.getElementById('btnHangup').onclick = () => {
  pc.close();
  window.close();
}

window.onload = () => {
  if (peer) startCall();
};
