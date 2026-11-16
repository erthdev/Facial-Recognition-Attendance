
/* FaceTrack API Client */
(() => {
  'use strict';

  const baseURL = (
    window.FACETRACK_API_BASE_URL ||
    'http://127.0.0.1:8000/api'
  ).replace(/\/$/, '');

  async function request(path, options = {}) {
    let response;

    try {
      response = await fetch(`${baseURL}${path}`, {
        ...options,
        headers: {
          ...(options.body
            ? { 'Content-Type': 'application/json' }
            : {}),
          ...options.headers
        }
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

    getDashboard() {
      return request('/dashboard');
    },

    getStudents() {
      return request('/students');
    },

    createStudent(student) {
      return request('/students', {
        method: 'POST',
        body: JSON.stringify(student)
      });
    },

    getAttendance(filters = {}) {
      return request(`/attendance${queryString(filters)}`);
    },

    getReports(filters = {}) {
      return request(`/reports${queryString(filters)}`);
    }
  };
})();
