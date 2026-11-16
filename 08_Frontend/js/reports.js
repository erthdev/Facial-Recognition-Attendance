/* Report filters and CSV export for the current table. */
document.addEventListener('DOMContentLoaded', () => {
  const panel = document.querySelector('.report-filter-panel'); if (!panel) return;
  const selects = [...panel.querySelectorAll('select')], dates = [...panel.querySelectorAll('input[type="date"]')];
  const buttons = [...panel.querySelectorAll('button')];
  const reset = buttons.find(b => /reset/i.test(b.textContent));
  const generate = buttons.find(b => /generate/i.test(b.textContent));
  const table = document.querySelector('.recent-panel table');
  reset?.addEventListener('click', () => {
    selects.forEach(s => s.selectedIndex = 0); dates.forEach(d => d.value = '');
    [...(table?.tBodies[0]?.rows || [])].forEach(row => row.hidden = false);
    FaceTrack.toast('Report filters reset.');
  });
  generate?.addEventListener('click', async () => {
    const filters = { report_type:selects[0]?.value || '', start_date:dates[0]?.value || '', end_date:dates[1]?.value || '', status:selects[1]?.value || '' };
    if (filters.start_date && filters.end_date && filters.start_date > filters.end_date) { FaceTrack.toast('Start date cannot be later than end date.', 'error'); return; }
    try {
      const result = await FaceTrackAPI.getReports(filters);
      if (Array.isArray(result.records) && table?.tBodies[0]) {
        const safe = v => String(v ?? '—').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]);
        table.tBodies[0].innerHTML = result.records.map(r => `<tr>${[r.full_name || r.name,r.student_id,r.date,r.time_in,r.status].map(v => `<td>${safe(v)}</td>`).join('')}</tr>`).join('');
      }
      FaceTrack.toast('Report data loaded from the backend.', 'success');
    } catch {
      const wanted = filters.status.toLowerCase();
      [...(table?.tBodies[0]?.rows || [])].forEach(row => { const status = row.cells[4]?.textContent.trim().toLowerCase(); row.hidden = !!wanted && wanted !== 'all statuses' && status !== wanted; });
      FaceTrack.toast('Showing sample records. Connect the Python API for live reports.');
    }
  });
  const exportButton = document.createElement('button'); exportButton.type = 'button'; exportButton.className = 'button button-outline'; exportButton.textContent = 'Export CSV';
  (document.querySelector('.recent-panel .table-tools') || document.querySelector('.recent-panel .panel-header'))?.append(exportButton);
  exportButton.addEventListener('click', () => {
    if (!table) return;
    const rows = [
      [...(table.tHead?.rows[0]?.cells || [])].map(c => c.textContent.trim()),
      ...[...(table.tBodies[0]?.rows || [])].filter(r => !r.hidden).map(r => [...r.cells].map(c => c.textContent.trim()))
    ];
    const csv = rows.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type:'text/csv;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `facetrack-report-${new Date().toISOString().slice(0,10)}.csv`; link.click(); URL.revokeObjectURL(url);
  });
});
