/* Student details form. Demo entries stay in this browser only; no face data is stored. */
(() => {
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]);
  document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.form-panel form'); if (!form) return;
    const fields = [...form.querySelectorAll('input, select')];
    const button = form.querySelector('button'); if (!button) return;
    const tbody = document.querySelector('.enrolled-panel tbody');
    function render(students) {
      if (!tbody) return;
      tbody.innerHTML = students.slice(0, 8).map(s => {
        const name = escapeHTML(s.full_name); const id = escapeHTML(s.student_id);
        return `<tr><td><div class="student-cell"><div class="avatar avatar-purple">${FaceTrack.initials(name)}</div><span><strong>${name}</strong><small>${escapeHTML(s.email || '')}</small></span></div></td><td>${id}</td><td>${escapeHTML(s.course || '—')}</td><td>${FaceTrack.date(s.enrolled_at)}</td><td><span class="status status-neutral">Not captured</span></td></tr>`;
      }).join('');
    }
    button.addEventListener('click', async () => {
      const [id, first, last, email, course, year] = fields.map(f => f.value.trim());
      if (!id || !first || !last) { FaceTrack.toast('Student ID, first name, and last name are required.', 'error'); fields[!id ? 0 : !first ? 1 : 2].focus(); return; }
      if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { FaceTrack.toast('Enter a valid email address.', 'error'); fields[3].focus(); return; }
      const student = { student_id:id, first_name:first, last_name:last, full_name:`${first} ${last}`, email, course, year_level:year, enrolled_at:new Date().toISOString() };
      try {
        await FaceTrackAPI.createStudent(student);
        FaceTrack.toast('Student details submitted to the backend.', 'success');
      } catch {
        const list = FaceTrack.read('students', []);
        if (list.some(s => s.student_id === id)) { FaceTrack.toast('That student ID is already in the local demo list.', 'error'); return; }
        list.unshift(student); FaceTrack.write('students', list); render(list);
        FaceTrack.toast('Saved in this browser demo only. Face data has not been enrolled.', 'success');
      }
    });
    render(FaceTrack.read('students', []));
  });
})();
