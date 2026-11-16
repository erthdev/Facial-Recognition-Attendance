/* Dashboard: loads real KPI values when the future API is available. */
document.addEventListener('DOMContentLoaded', async () => {
  if (!document.querySelector('.stats-grid') || !window.FaceTrackAPI) return;
  try {
    const data = await FaceTrackAPI.getDashboard();
    const values = [data.total_students, data.present_today, data.late_today, data.absent_today];
    document.querySelectorAll('.stats-grid .stat-value').forEach((el, i) => {
      if (values[i] != null) el.textContent = Number(values[i]).toLocaleString();
    });
  } catch (error) { console.info('[FaceTrack] API unavailable; showing illustrative dashboard data.', error.message); }
});
