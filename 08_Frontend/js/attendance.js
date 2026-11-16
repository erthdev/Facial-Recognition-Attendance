
document.addEventListener('DOMContentLoaded', () => {
  // --------------------------------------------------
  // ELEMENTS
  // --------------------------------------------------

  const stage = document.getElementById('cameraStage');
  const startButton = document.getElementById('startCameraButton');
  const captureButton = document.getElementById('captureButton');
  const cameraStatus = document.getElementById('cameraStatus');

  const resultPanel = document.getElementById('recognitionResult');
  const distanceDisplay = document.getElementById('recognitionDistance');
  const attendanceStatus = document.getElementById('attendanceStatus');
  const messageDisplay = document.getElementById('recognitionMessage');

  const attendanceBody = document.getElementById('todayAttendanceBody');
  const dateDisplay = document.getElementById('attendanceDate');

  if (!stage || !startButton || !captureButton) return;

  // --------------------------------------------------
  // STATE
  // --------------------------------------------------

  const API_BASE = 'http://127.0.0.1:8000/api';

  let stream = null;
  let video = null;
  let processing = false;

  const today = new Date();
  const todayString = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0')
  ].join('-');

  if (dateDisplay) {
    dateDisplay.textContent = today.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  // --------------------------------------------------
  // HELPERS
  // --------------------------------------------------

  function notify(message, type = 'success') {
    if (window.FaceTrack?.toast) {
      FaceTrack.toast(message, type);
    } else {
      console.log(message);
    }
  }

  function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    })[char]);
  }

  function initials(name) {
    return String(name || 'Student')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(part => part[0])
      .join('')
      .toUpperCase();
  }

  function formatTime(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return value || '—';

    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function setCameraStatus(active) {
    if (!cameraStatus) return;

    cameraStatus.innerHTML = active
      ? '<i></i> CAMERA ACTIVE'
      : '<i></i> CAMERA OFFLINE';
  }

  // --------------------------------------------------
  // CAMERA
  // --------------------------------------------------

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      notify('Camera access requires localhost or HTTPS.', 'error');
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });

      video = document.createElement('video');
      video.autoplay = true;
      video.playsInline = true;
      video.muted = true;

      video.style.cssText = `
        display: block;
        width: 100%;
        height: 100%;
        min-height: 280px;
        object-fit: cover;
        border-radius: 14px;
        background: #101827;
        transform: scaleX(-1);
      `;

      video.srcObject = stream;
      stage.replaceChildren(video);

      await video.play();

      startButton.textContent = 'Stop camera';
      captureButton.disabled = false;

      setCameraStatus(true);

      notify('Camera is ready. Position the student and capture.', 'success');

    } catch (error) {
      stopCamera();

      notify(
        error.name === 'NotAllowedError'
          ? 'Camera permission was denied. Allow camera access in your browser.'
          : `Could not start camera: ${error.message}`,
        'error'
      );
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }

    stream = null;
    video = null;

    const placeholder = document.createElement('div');
    placeholder.className = 'camera-placeholder';

    placeholder.innerHTML = `
      <div class="camera-symbol">◎</div>
      <strong>Camera preview</strong>
      <span>Connect the camera to begin face recognition.</span>
      <div class="camera-frame">
        <i></i><i></i><i></i><i></i>
      </div>
    `;

    stage.replaceChildren(placeholder);

    startButton.textContent = '◎ Start camera';
    captureButton.disabled = true;

    setCameraStatus(false);
  }

  startButton.addEventListener('click', () => {
    if (stream) {
      stopCamera();
    } else {
      startCamera();
    }
  });

  // --------------------------------------------------
  // CAPTURE IMAGE
  // --------------------------------------------------

  function captureImage() {
    if (!video || !video.videoWidth || !video.videoHeight) {
      throw new Error('Camera is not ready. Please try again.');
    }

    const canvas = document.createElement('canvas');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext('2d');

    // Mirror the captured image to match the preview.
    context.translate(canvas.width, 0);
    context.scale(-1, 1);

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error('Could not capture camera image.'));
        }
      }, 'image/jpeg', 0.90);
    });
  }

  // --------------------------------------------------
  // FACIAL RECOGNITION API
  // --------------------------------------------------

  async function recognizeStudent() {
    if (processing) return;

    processing = true;
    captureButton.disabled = true;
    captureButton.textContent = 'Recognizing...';

    try {
      const imageBlob = await captureImage();

      const formData = new FormData();

      formData.append('image', imageBlob, 'attendance.jpg');
      formData.append('session_label', 'Default');

      const response = await fetch(
        `${API_BASE}/attendance/recognize`,
        {
          method: 'POST',
          body: formData
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || 'Recognition request failed.'
        );
      }

      displayRecognition(data);

      if (data.recorded) {
        notify(data.message, 'success');
        await loadTodayAttendance();
      } else if (data.outcome === 'Unknown') {
        notify('No enrolled student was recognized.', 'error');
      } else {
        notify(data.message, 'info');
      }

    } catch (error) {
      console.error('Recognition error:', error);

      messageDisplay.textContent = error.message;

      notify(error.message, 'error');

    } finally {
      processing = false;
      captureButton.disabled = !stream;
      captureButton.textContent = 'Capture & identify';
    }
  }

  captureButton.addEventListener('click', recognizeStudent);

  // --------------------------------------------------
  // DISPLAY RECOGNITION RESULT
  // --------------------------------------------------

  function displayRecognition(data) {
    const person = data.person;

    const outcome = data.outcome;

    const statusClasses = {
      Present: 'status-present',
      Late: 'status-late',
      Duplicate: 'status-neutral',
      Unknown: 'status-neutral'
    };

    const statusLabels = {
      Present: 'Present',
      Late: 'Late',
      Duplicate: 'Already recorded',
      Unknown: 'Not recognized'
    };

    if (distanceDisplay) {
      distanceDisplay.textContent =
        Number.isFinite(data.distance)
          ? Number(data.distance).toFixed(4)
          : '—';
    }

    if (attendanceStatus) {
      attendanceStatus.className =
        `status ${statusClasses[outcome] || 'status-neutral'}`;

      attendanceStatus.textContent =
        statusLabels[outcome] || outcome;
    }

    if (!person) {
      resultPanel.innerHTML = `
        <div class="empty-face">?</div>
        <strong>Unknown student</strong>
        <p>No matching enrolled student was found.</p>
      `;

      messageDisplay.textContent = data.message;
      return;
    }

    resultPanel.innerHTML = `
      <div class="student-cell">
        <div class="avatar avatar-blue">
          ${escapeHTML(initials(person.full_name))}
        </div>

        <span>
          <strong>${escapeHTML(person.full_name)}</strong>
          <small>${escapeHTML(person.student_no)}</small>
        </span>
      </div>

      <div class="recognition-student-details">
        <p><strong>Section:</strong> ${escapeHTML(person.section || '—')}</p>
        <p><strong>Student ID:</strong> ${escapeHTML(person.student_no)}</p>
        <p><strong>Result:</strong> ${escapeHTML(outcome)}</p>
      </div>
    `;

    messageDisplay.textContent = data.message;
  }

  // --------------------------------------------------
  // LOAD TODAY'S ATTENDANCE
  // --------------------------------------------------

  async function loadTodayAttendance() {
    if (!attendanceBody) return;

    try {
      const params = new URLSearchParams({
        start_date: todayString,
        end_date: todayString
      });

      const response = await fetch(
        `${API_BASE}/attendance?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error('Could not load attendance records.');
      }

      const records = await response.json();

      if (!records.length) {
        attendanceBody.innerHTML = `
          <tr>
            <td colspan="5">No attendance records for today yet.</td>
          </tr>
        `;
        return;
      }

      attendanceBody.innerHTML = records.map(record => `
        <tr>
          <td>
            <div class="student-cell">
              <div class="avatar avatar-blue">
                ${escapeHTML(initials(record.full_name))}
              </div>

              <span>
                <strong>${escapeHTML(record.full_name)}</strong>
                <small>${escapeHTML(record.section || '—')}</small>
              </span>
            </div>
          </td>

          <td>${escapeHTML(record.student_no)}</td>

          <td>${escapeHTML(formatTime(record.scanned_at))}</td>

          <td>
            <span class="status ${
              record.status === 'Present'
                ? 'status-present'
                : 'status-late'
            }">
              ${escapeHTML(record.status)}
            </span>
          </td>

          <td>
            <span class="confidence-label">
              ${Number(record.distance).toFixed(4)}
            </span>
          </td>
        </tr>
      `).join('');

    } catch (error) {
      console.error('Attendance loading error:', error);

      attendanceBody.innerHTML = `
        <tr>
          <td colspan="5">Unable to load attendance records.</td>
        </tr>
      `;
    }
  }

  // --------------------------------------------------
  // INITIALIZATION
  // --------------------------------------------------

  loadTodayAttendance();

  window.addEventListener('pagehide', () => {
    stream?.getTracks().forEach(track => track.stop());
  });
});
