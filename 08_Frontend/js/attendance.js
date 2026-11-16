/* Webcam preview only. Actual face matching and attendance recording belong in Python. */
document.addEventListener('DOMContentLoaded', () => {
  const stage = document.querySelector('.camera-stage'); if (!stage) return;
  const start = document.querySelector('.camera-controls .button-primary');
  const capture = document.querySelector('.camera-controls .button-outline');
  const status = document.querySelector('.live-indicator');
  const placeholder = stage.querySelector('.camera-placeholder');
  let stream = null, video = null;
  if (!start) return;
  function stop() {
    stream?.getTracks().forEach(track => track.stop()); stream = null; video = null;
    stage.replaceChildren(); if (placeholder) stage.append(placeholder);
    start.textContent = '◎ Start camera'; if (capture) capture.disabled = true;
    if (status) status.innerHTML = '<i></i> CAMERA OFFLINE';
  }
  start.addEventListener('click', async () => {
    if (stream) { stop(); return; }
    if (!navigator.mediaDevices?.getUserMedia) { FaceTrack.toast('Camera access requires localhost or HTTPS and a supported browser.', 'error'); return; }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user' }, audio:false });
      video = document.createElement('video'); video.autoplay = true; video.playsInline = true; video.muted = true;
      video.style.cssText = 'display:block;width:100%;height:100%;min-height:280px;object-fit:cover;border-radius:14px;background:#101827';
      video.srcObject = stream; stage.replaceChildren(video); start.textContent = 'Stop camera';
      if (capture) capture.disabled = false; if (status) status.innerHTML = '<i></i> CAMERA ACTIVE';
      FaceTrack.toast('Camera preview is active. Face recognition is not connected yet.', 'success');
    } catch (error) { stream = null; FaceTrack.toast(error.name === 'NotAllowedError' ? 'Camera permission was denied. Allow camera access in your browser.' : `Could not start camera: ${error.message}`, 'error'); }
  });
  capture?.addEventListener('click', () => FaceTrack.toast('Camera preview works; face matching must be handled by the Python backend.'));
  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
});
