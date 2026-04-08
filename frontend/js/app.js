const SESSION_ID = 'sess-' + Math.random().toString(36).slice(2, 10);
const BACKEND = 'http://localhost:9000';

let isSpeaking = false;
let isPaused = false;
let audioContext = null;
let currentSource = null;
let audioQueue = [];
let isPlayingAudio = false;
let headerSkipped = false;
let isReceivingAudio = false;
let playbackSessionId = 0;
let hasStartedChat = false;
let webSpeechSynth = null;
let webSpeechUtterance = null;

function showChatUI() {
  if (!hasStartedChat) {
    hasStartedChat = true;
    document.getElementById('welcome-section').style.display = 'none';
    document.getElementById('chat-section').classList.remove('d-none');
  }
}

function setStatus(msg) {
  document.getElementById('status-bar').textContent = msg;
}

function appendMessage(role, text) {
  showChatUI();
  const box = document.getElementById('chat-box');
  const div = document.createElement('div');
  div.className = role === 'user' ? 'msg-user' : 'msg-ai';
  const bubble = document.createElement('span');
  bubble.className = 'bubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function showPauseBtn(show) {
  const btn = document.getElementById('btn-pause-speech');
  if (show) {
    btn.classList.remove('d-none');
    btn.innerHTML = '&#9208;';
    btn.title = '暂停朗读';
  } else {
    btn.classList.add('d-none');
  }
}

function updatePauseIcon(paused) {
  const btn = document.getElementById('btn-pause-speech');
  if (paused) {
    btn.innerHTML = '&#9654;';
    btn.title = '继续朗读';
  } else {
    btn.innerHTML = '&#9208;';
    btn.title = '暂停朗读';
  }
}

function initAudioContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
  }
  return audioContext;
}

function queueAudioChunk(pcmChunk) {
  if (!headerSkipped && pcmChunk.length > 44) {
    pcmChunk = pcmChunk.slice(44);
    headerSkipped = true;
  }

  if (pcmChunk.length === 0) return;

  audioQueue.push(pcmChunk);

  if (!isPlayingAudio) {
    isPlayingAudio = true;
    playNextChunk();
  }
}

function playNextChunk() {
  if (!isPlayingAudio) return;

  if (audioQueue.length === 0) {
    if (!isReceivingAudio) {
      isPlayingAudio = false;
      isSpeaking = false;
      showPauseBtn(false);
      setStatus('点击麦克风开始说话');
      headerSkipped = false;
    }
    return;
  }

  if (currentSource) return;

  const ctx = initAudioContext();
  if (ctx.state === 'suspended') {
    ctx.resume();
  }

  const currentSessionId = playbackSessionId;

  const chunk = audioQueue.shift();
  const int16 = new Int16Array(chunk.buffer, chunk.byteOffset, chunk.length / 2);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32768.0;
  }

  const audioBuffer = ctx.createBuffer(1, float32.length, 24000);
  audioBuffer.getChannelData(0).set(float32);

  const source = ctx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(ctx.destination);
  source.onended = () => {
    if (playbackSessionId !== currentSessionId) return;
    currentSource = null;
    playNextChunk();
  };

  currentSource = source;
  source.start();
}

function stopStreamingAudio() {
  if (currentTTSController) {
    currentTTSController.abort();
    currentTTSController = null;
  }
  isPlayingAudio = false;
  isReceivingAudio = false;
  audioQueue = [];
  headerSkipped = false;
  playbackSessionId++;
  if (currentSource) {
    try {
      currentSource.onended = null;
      currentSource.disconnect();
      currentSource.stop();
    } catch (e) {}
    currentSource = null;
  }
  if (audioContext) {
    try {
      audioContext.close();
    } catch (e) {}
    audioContext = null;
  }
}

let currentTTSController = null;

async function playStreamingTTS(text) {
  stopStreamingAudio();
  const mySessionId = ++playbackSessionId;
  isReceivingAudio = true;
  isSpeaking = true;
  headerSkipped = false;

  setStatus('正在合成语音...');

  try {
    currentTTSController = new AbortController();
    const response = await fetch(`${BACKEND}/api/tts/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal: currentTTSController.signal,
    });

    if (!response.ok) {
      throw new Error('TTS stream failed');
    }

    const reader = response.body.getReader();
    showPauseBtn(true);
    setStatus('正在播放回答...');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (playbackSessionId !== mySessionId) return;
      queueAudioChunk(new Uint8Array(value));
    }

    if (playbackSessionId !== mySessionId) return;
    isReceivingAudio = false;
    currentTTSController = null;

  } catch (e) {
    if (e.name === 'AbortError') {
      return;
    }
    console.error('Streaming TTS error:', e);
    if (playbackSessionId !== mySessionId) return;
    setStatus('语音播放失败');
    stopStreamingAudio();
    isSpeaking = false;
    showPauseBtn(false);
    setStatus('点击麦克风开始说话');
  }
}

function togglePauseSpeech() {
  if (!isSpeaking) return;
  
  if (webSpeechSynth && webSpeechUtterance) {
    togglePauseWebSpeech();
  } else if (audioContext) {
    if (isPaused) {
      audioContext.resume();
      isPaused = false;
      updatePauseIcon(false);
      setStatus('正在播放回答...');
    } else {
      audioContext.suspend();
      isPaused = true;
      updatePauseIcon(true);
      setStatus('朗读已暂停');
    }
  }
}

function stopSpeech() {
  stopStreamingAudio();
  stopWebSpeech();
  isSpeaking = false;
  isPaused = false;
  showPauseBtn(false);
  setStatus('点击麦克风开始说话');
}

function stopWebSpeech() {
  if (webSpeechSynth) {
    webSpeechSynth.cancel();
  }
  webSpeechUtterance = null;
}

function playWebSpeech(text) {
  stopStreamingAudio();
  stopWebSpeech();
  
  if (!window.speechSynthesis) {
    console.log('WebSpeech API not supported');
    setStatus('浏览器不支持语音合成');
    isSpeaking = false;
    showPauseBtn(false);
    return;
  }
  
  console.log('[WebSpeech] Starting fallback playback');
  webSpeechSynth = window.speechSynthesis;
  webSpeechUtterance = new SpeechSynthesisUtterance(text);
  
  webSpeechUtterance.lang = 'zh-CN';
  webSpeechUtterance.rate = 1.0;
  webSpeechUtterance.pitch = 1.0;
  webSpeechUtterance.volume = 1.0;
  
  isSpeaking = true;
  showPauseBtn(true);
  setStatus('正在播放回答...');
  
  webSpeechUtterance.onend = () => {
    console.log('[WebSpeech] Playback ended');
    isSpeaking = false;
    isPaused = false;
    showPauseBtn(false);
    setStatus('点击麦克风开始说话');
  };
  
  webSpeechUtterance.onerror = (e) => {
    console.log('[WebSpeech] Error:', e);
    isSpeaking = false;
    showPauseBtn(false);
    setStatus('语音播放失败');
  };
  
  webSpeechSynth.speak(webSpeechUtterance);
}

function togglePauseWebSpeech() {
  if (!webSpeechSynth || !webSpeechUtterance) return;
  
  if (isPaused) {
    webSpeechSynth.resume();
    isPaused = false;
    updatePauseIcon(false);
    setStatus('正在播放回答...');
  } else {
    webSpeechSynth.pause();
    isPaused = true;
    updatePauseIcon(true);
    setStatus('朗读已暂停');
  }
}

let currentAIMsgDiv = null;
let currentAIMsgBubble = null;
let currentAIText = '';

WSClient.connect(
  SESSION_ID,
  (msg) => {
    showChatUI();
    appendMessage('user', msg.user_text);
    currentAIText = '';
    currentAIMsgDiv = document.createElement('div');
    currentAIMsgDiv.className = 'msg-ai';
    currentAIMsgBubble = document.createElement('span');
    currentAIMsgBubble.className = 'bubble';
    currentAIMsgDiv.appendChild(currentAIMsgBubble);
    document.getElementById('chat-box').appendChild(currentAIMsgDiv);
  },
  (msg) => {
    if (currentAIMsgBubble) {
      currentAIText += msg.text;
      currentAIMsgBubble.textContent = currentAIText;
      document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight;
    }
  },
  () => {
    console.log('Text ended, preparing audio playback');
    audioQueue = [];
    headerSkipped = false;
    isReceivingAudio = true;
    isSpeaking = true;
    showPauseBtn(true);
    setStatus('正在合成语音...');
  },
  (arrayBuffer) => {
    console.log('Audio chunk received, size:', arrayBuffer.byteLength, 'bytes');
    queueAudioChunk(new Uint8Array(arrayBuffer));
  },
  (err) => {
    setStatus('错误: ' + err);
  },
  () => {
    console.log('Audio stream ended');
    isReceivingAudio = false;
    playNextChunk();
  },
  (error) => {
    console.log('TTS error:', error);
    stopStreamingAudio();
    setStatus(error);
    isSpeaking = false;
    showPauseBtn(false);
    setStatus('点击麦克风开始说话');
  },
  (text) => {
    console.log('TTS fallback to WebSpeech');
    playWebSpeech(text);
  }
);

const btnRecord = document.getElementById('btn-record');
const btnStop = document.getElementById('btn-stop');
const btnPauseSpeech = document.getElementById('btn-pause-speech');

btnRecord.addEventListener('click', async () => {
  try {
    stopSpeech();
    btnRecord.classList.add('recording');
    btnStop.classList.remove('d-none');
    await AudioRecorder.start((blob) => {
      setStatus('识别中，请稍候...');
      WSClient.sendAudio(blob);
    });
    setStatus('录音中，点击停止...');
  } catch (e) {
    setStatus('无法访问麦克风，请检查浏览器权限');
    btnRecord.classList.remove('recording');
    btnStop.classList.add('d-none');
  }
});

btnStop.addEventListener('click', () => {
  AudioRecorder.stop();
  btnRecord.classList.remove('recording');
  btnStop.classList.add('d-none');
  setStatus('处理中...');
});

btnPauseSpeech.addEventListener('click', togglePauseSpeech);

document.getElementById('btn-send').addEventListener('click', sendText);
document.getElementById('text-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendText();
});

async function sendText() {
  stopSpeech();
  const input = document.getElementById('text-input');
  const question = input.value.trim();
  if (!question) return;
  input.value = '';
  appendMessage('user', question);
  setStatus('AI思考中...');
  try {
    const chatResp = await fetch(`${BACKEND}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: SESSION_ID }),
    });
    if (!chatResp.ok) throw new Error(`HTTP ${chatResp.status}`);
    const data = await chatResp.json();
    appendMessage('ai', data.answer);

    playStreamingTTS(data.answer);
  } catch (e) {
    setStatus('请求失败：' + e.message);
  }
}
