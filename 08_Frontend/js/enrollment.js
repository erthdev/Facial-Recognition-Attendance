
/* FaceTrack - Student and Biometric Enrollment */
(() => {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    const $ = (selector) => document.querySelector(selector);

    const form = $('#studentEnrollmentForm');
    const capturePanel = $('#faceCapturePanel');
    const formPanel = $('#studentFormPanel');
    const video = $('#webcamVideo');
    const placeholder = $('#cameraPlaceholder');
    const gallery = $('#sampleGallery');
    const tbody = $('#studentsTableBody');

    if (!form || !window.FaceTrackAPI) return;

    const MIN_SAMPLES = 3;
    const MAX_SAMPLES = 5;

    let currentPersonId = null;
    let currentStudent = null;
    let cameraStream = null;
    let samples = [];

    const escapeHTML = (value) =>
      String(value ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[c]);

    function message(element, text, type = '') {
      if (!element) return;

      element.textContent = text;
      element.className = type;
    }

    function stopCamera() {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
      }

      if (video) {
        video.srcObject = null;
      }

      $('#captureButton').disabled = true;
      $('#stopCameraButton').disabled = true;
      $('#startCameraButton').disabled = false;

      if (placeholder) placeholder.hidden = false;
    }

    function updateProgress() {
      const count = samples.length;

      $('#sampleCount').textContent =
        `${count} / ${MIN_SAMPLES} minimum`;

      $('#sampleProgressBar').style.width =
        `${(count / MAX_SAMPLES) * 100}%`;

      $('#captureButton').disabled =
        !cameraStream || count >= MAX_SAMPLES;

      $('#clearSamplesButton').disabled = count === 0;

      $('#submitFaceEnrollmentButton').disabled =
        count < MIN_SAMPLES;
    }

    function renderSamples() {
      if (!samples.length) {
        gallery.innerHTML =
          '<p class="panel-subtitle">Your captured images will appear here.</p>';

        updateProgress();
        return;
      }

      gallery.innerHTML = samples.map((sample, index) => `
        <div class="sample-card">
          <img src="${sample.preview}" alt="Face sample ${index + 1}">
          <span>Sample ${index + 1}</span>
          <button type="button" data-remove="${index}"
            aria-label="Remove sample ${index + 1}">×</button>
        </div>
      `).join('');

      updateProgress();
    }

    async function loadStudents() {
      try {
        const students = await FaceTrackAPI.getStudents();

        if (!Array.isArray(students) || !students.length) {
          tbody.innerHTML = `
            <tr><td colspan="5">No students registered yet.</td></tr>
          `;
          return;
        }

        tbody.innerHTML = students.slice(0, 8).map(student => {
          const name = escapeHTML(student.full_name);
          const id = escapeHTML(student.student_id);
          const section = escapeHTML(student.section || '—');
          const enrolled = student.biometric_enrolled;

          return `
            <tr>
              <td>
                <div class="student-cell">
                  <div class="avatar avatar-purple">
                    ${escapeHTML(FaceTrack.initials(student.full_name))}
                  </div>
                  <span><strong>${name}</strong></span>
                </div>
              </td>
              <td>${id}</td>
              <td>${section}</td>
              <td>${escapeHTML(FaceTrack.date(student.created_at))}</td>
              <td>
                <span class="status ${enrolled ? 'status-present' : 'status-neutral'}">
                  ${enrolled ? 'Enrolled' : 'Pending'}
                </span>
              </td>
            </tr>
          `;
        }).join('');

      } catch (error) {
        tbody.innerHTML = `
          <tr><td colspan="5">Unable to load students: ${escapeHTML(error.message)}</td></tr>
        `;
      }
    }

    // STEP 1: REGISTER STUDENT
    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      const studentId = $('#studentId').value.trim();
      const firstName = $('#firstName').value.trim();
      const lastName = $('#lastName').value.trim();
      const course = $('#course').value;
      const year = $('#yearLevel').value;
      const consent = $('#consentGiven').checked;

      if (!studentId || !firstName || !lastName || !consent) {
        message(
          $('#studentFormMessage'),
          'Complete all required fields and confirm consent.'
        );
        return;
      }

      const button = $('#registerStudentButton');
      button.disabled = true;
      button.textContent = 'Registering...';

      try {
        const student = await FaceTrackAPI.createStudent({
          student_id: studentId,
          first_name: firstName,
          last_name: lastName,
          section: [course, year].filter(Boolean).join(' - ') || null,
          consent_given: true,
          consent_date: new Date().toISOString().slice(0, 10)
        });

        currentPersonId = student.person_id;
        currentStudent = {
          name: `${firstName} ${lastName}`,
          id: studentId
        };

        $('#captureStudentName').textContent =
          `Capturing samples for ${currentStudent.name}`;

        formPanel.hidden = true;
        capturePanel.hidden = false;

        message(
          $('#captureMessage'),
          'Student registered successfully. Start the camera to capture samples.'
        );

        await loadStudents();

      } catch (error) {
        message($('#studentFormMessage'), error.message);
      } finally {
        button.disabled = false;
        button.innerHTML = 'Register and continue <span>→</span>';
      }
    });

    // STEP 2: START WEBCAM
    $('#startCameraButton').addEventListener('click', async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error('Webcam access is unavailable. Use localhost or HTTPS.');
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });

        video.srcObject = cameraStream;
        await video.play();

        placeholder.hidden = true;

        $('#captureButton').disabled = false;
        $('#stopCameraButton').disabled = false;
        $('#startCameraButton').disabled = true;

        message($('#captureMessage'), 'Camera is ready. Position your face in the frame.');

      } catch (error) {
        stopCamera();
        message($('#captureMessage'), error.message);
      }
    });

    // STEP 3: CAPTURE FACE SAMPLE
    $('#captureButton').addEventListener('click', () => {
      if (!cameraStream || !video.videoWidth) {
        message($('#captureMessage'), 'Camera is not ready.');
        return;
      }

      if (samples.length >= MAX_SAMPLES) return;

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const context = canvas.getContext('2d');

      // Mirror the preview so the saved image matches the displayed view.
      context.translate(canvas.width, 0);
      context.scale(-1, 1);
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        if (!blob) {
          message($('#captureMessage'), 'Unable to capture image.');
          return;
        }

        samples.push({
          blob,
          preview: URL.createObjectURL(blob)
        });

        renderSamples();

        message(
          $('#captureMessage'),
          `${samples.length} sample(s) captured. ${
            samples.length < MIN_SAMPLES
              ? `Capture ${MIN_SAMPLES - samples.length} more.`
              : 'You can submit your facial enrollment.'
          }`
        );

      }, 'image/jpeg', 0.92);
    });

    // REMOVE INDIVIDUAL SAMPLE
    gallery.addEventListener('click', (event) => {
      const button = event.target.closest('[data-remove]');
      if (!button) return;

      const index = Number(button.dataset.remove);
      const sample = samples[index];

      if (sample) URL.revokeObjectURL(sample.preview);

      samples.splice(index, 1);
      renderSamples();

      message($('#captureMessage'), 'Sample removed.');
    });

    // CLEAR ALL SAMPLES
    $('#clearSamplesButton').addEventListener('click', () => {
      samples.forEach(sample => URL.revokeObjectURL(sample.preview));
      samples = [];

      renderSamples();
      message($('#captureMessage'), 'All captured samples cleared.');
    });

    // STOP CAMERA
    $('#stopCameraButton').addEventListener('click', () => {
      stopCamera();
      message($('#captureMessage'), 'Camera stopped.');
    });

    // STEP 4: SUBMIT FACIAL ENROLLMENT
    $('#submitFaceEnrollmentButton').addEventListener('click', async () => {
      if (!currentPersonId || samples.length < MIN_SAMPLES) return;

      const button = $('#submitFaceEnrollmentButton');
      button.disabled = true;
      button.textContent = 'Processing facial samples...';

      stopCamera();

      try {
        const result = await FaceTrackAPI.enrollFace(
          currentPersonId,
          samples.map(sample => sample.blob)
        );

        const status = await FaceTrackAPI.getBiometricStatus(currentPersonId);

        message(
          $('#captureMessage'),
          `${result.message} ${status.samples} facial samples saved.`,
          'success'
        );

        samples.forEach(sample => URL.revokeObjectURL(sample.preview));
        samples = [];

        renderSamples();
        await loadStudents();

        button.textContent = 'Enrollment completed';

      } catch (error) {
        message(
          $('#captureMessage'),
          `Enrollment failed: ${error.message}`
        );

        button.disabled = false;
        button.textContent = 'Retry facial enrollment →';
      }
    });

    // CLEAN UP CAMERA WHEN LEAVING PAGE
    window.addEventListener('pagehide', stopCamera);

    // INITIALIZE
    renderSamples();
    loadStudents();
  });
})();
