
/* FaceTrack API Client */
(() => {
  'use strict';

  const baseURL = (
    window.FACETRACK_API_BASE_URL ||
    'http://127.0.0.1:8000/api'
  ).replace(/\/$/, '');

  async function request(path, options = {}) {
    let response;

    const headers = { ...options.headers };
    const isFormData = options.body instanceof FormData;

    // Let the browser generate the multipart Content-Type boundary.
    if (options.body && !isFormData && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      response = await fetch(`${baseURL}${path}`, {
        ...options,
        headers
      });
    } catch (error) {
      throw new Error(
        'Cannot connect to FaceTrack API. Check that the backend is running.'
      );
    }

    const contentType = response.headers.get('content-type') || '';

    const data = contentType.includes('application/json')
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const message =
        typeof data === 'object' && data !== null
          ? data.detail || `Request failed (${response.status})`
          : data || `Request failed (${response.status})`;

      throw new Error(message);
    }

    return data;
  }

  function queryString(filters = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value);
      }
    });

    const query = params.toString();
    return query ? `?${query}` : '';
  }

  window.FaceTrackAPI = {
    baseURL,
    request,

    // Dashboard
    getDashboard() {
      return request('/dashboard');
    },

    // Student management
    getStudents() {
      return request('/students');
    },

    createStudent(student) {
      return request('/students', {
        method: 'POST',
        body: JSON.stringify(student)
      });
    },

    // Biometric enrollment status
    getBiometricStatus(personId) {
      return request(`/students/${personId}/biometric-status`);
    },

    // Upload facial image samples
    enrollFace(personId, images) {
      const formData = new FormData();

      images.forEach((image, index) => {
        formData.append(
          'images',
          image,
          `face-sample-${index + 1}.jpg`
        );
      });

      return request(`/students/${personId}/enroll-face`, {
        method: 'POST',
        body: formData
      });
    },

    // Attendance
    getAttendance(filters = {}) {
      return request(`/attendance${queryString(filters)}`);
    },

    // Reports
    getReports(filters = {}) {
      return request(`/reports${queryString(filters)}`);
    }
  };
})();
