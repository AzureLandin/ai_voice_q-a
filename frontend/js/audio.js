const AudioRecorder = (() => {
  let mediaRecorder = null;
  let chunks = [];

  async function start(onStop) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    // Prefer webm, fall back to default
    const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
    const options = mimeType ? { mimeType } : {};
    mediaRecorder = new MediaRecorder(stream, options);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
      stream.getTracks().forEach((t) => t.stop());
      onStop(blob);
    };
    mediaRecorder.start();
  }

  function stop() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
  }

  return { start, stop };
})();
