const WSClient = (() => {
  let ws = null;
  let sessionId = null;
  let onTextStartCb = null;
  let onTextDeltaCb = null;
  let onTextEndCb = null;
  let onAudioCb = null;
  let onErrorCb = null;
  let onAudioEndCb = null;
  let onTTSErrorCb = null;
  let onTTSFallbackCb = null;
  let reconnectTimer = null;
  let connected = false;

  function connect(sid, onTextStart, onTextDelta, onTextEnd, onAudio, onError, onAudioEnd, onTTSError, onTTSFallback) {
    sessionId = sid;
    onTextStartCb = onTextStart;
    onTextDeltaCb = onTextDelta;
    onTextEndCb = onTextEnd;
    onAudioCb = onAudio;
    onErrorCb = onError;
    onAudioEndCb = onAudioEnd;
    onTTSErrorCb = onTTSError;
    onTTSFallbackCb = onTTSFallback;
    doConnect();
  }

  function doConnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    try {
      ws = new WebSocket(`ws://localhost:9000/ws/audio/${sessionId}`);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        connected = true;
        console.log('WebSocket已连接');
      };

      ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
if (msg.type === 'text_start') onTextStartCb(msg);
            else if (msg.type === 'text_delta') onTextDeltaCb(msg);
            else if (msg.type === 'text_end') onTextEndCb();
            else if (msg.type === 'tts_error') onTTSErrorCb(msg.error);
            else if (msg.type === 'tts_fallback') onTTSFallbackCb(msg.text);
            else if (msg.type === 'audio_end') onAudioEndCb();
            else if (msg.type === 'error') onErrorCb(msg.error);
          } catch (e) {
            onErrorCb('消息解析失败');
          }
        } else {
          onAudioCb(event.data);
        }
      };

      ws.onerror = () => {
        connected = false;
      };

      ws.onclose = () => {
        connected = false;
        console.log('WebSocket已断开，3秒后重连...');
        reconnectTimer = setTimeout(doConnect, 3000);
      };
    } catch (e) {
      connected = false;
      reconnectTimer = setTimeout(doConnect, 3000);
    }
  }

  function sendAudio(blob) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      if (onErrorCb) onErrorCb('WebSocket未连接，等待重连...');
      return;
    }
    blob.arrayBuffer().then((buf) => ws.send(buf));
  }

  function isConnected() {
    return connected && ws && ws.readyState === WebSocket.OPEN;
  }

  return { connect, sendAudio, isConnected };
})();
