/* Shared API client. The Python API will be connected in a later step. */
(() => {
  'use strict';
  const baseURL = (window.FACETRACK_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
  async function request(path, options = {}) {
    const response = await fetch(`${baseURL}${path}`, {
      ...options,
      headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers }
    });
    const type = response.headers.get('content-type') || '';
    const data = type.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) throw new Error(data?.detail || `Request failed (${response.status})`);
    return data;
  }
  window.FaceTrackAPI = {
    baseURL, request,
    getDashboard: () => request('/dashboard'),
    getStudents: () => request('/students'),
    createStudent: student => request('/students', { method: 'POST', body: JSON.stringify(student) }),
    getAttendance: filters => request(`/attendance${filters ? `?${new URLSearchParams(filters)}` : ''}`),
    recordAttendance: record => request('/attendance', { method: 'POST', body: JSON.stringify(record) }),
    getReports: filters => request(`/reports${filters ? `?${new URLSearchParams(filters)}` : ''}`)
  };
})();
