
document.addEventListener('DOMContentLoaded', () => {
  const API_BASE = 'http://127.0.0.1:8000/api';

  const startDate = document.getElementById('startDate');
  const endDate = document.getElementById('endDate');
  const statusFilter = document.getElementById('statusFilter');
  const reportType = document.getElementById('reportType');

  const generateButton = document.querySelector(
    '.report-filter-panel .button-primary'
  );

  const resetButton = document.querySelector(
    '.report-filter-panel .button-outline'
  );

  const exportButton = document.getElementById('exportReportButton');
  const searchInput = document.getElementById('recordSearch');
  const tableBody = document.getElementById('reportRecordsBody');
  const chartContainer = document.getElementById('attendanceTrendChart');

  if (!tableBody || !chartContainer) return;

  let allRecords = [];
  let visibleRecords = [];

  const escapeHTML = value =>
    String(value ?? '—').replace(/[&<>"']/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[char]);

  function localDateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  }

  function formatDate(value) {
    if (!value) return '—';

    const date = new Date(value.replace(' ', 'T'));

    if (Number.isNaN(date.getTime())) return value;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }

  function formatTime(value) {
    if (!value) return '—';

    const date = new Date(value.replace(' ', 'T'));

    if (Number.isNaN(date.getTime())) return '—';

    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getInitials(name) {
    return String(name || '?')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(part => part[0])
      .join('')
      .toUpperCase();
  }

  // UPDATE SUMMARY CARDS
  function updateSummary(summary = {}) {
    document.getElementById('totalCheckIns').textContent =
      summary.total_check_ins ?? 0;

    document.getElementById('presentCount').textContent =
      summary.present ?? 0;

    document.getElementById('lateCount').textContent =
      summary.late ?? 0;

    document.getElementById('uniqueStudents').textContent =
      summary.unique_students ?? 0;
  }

  // RENDER ATTENDANCE CHART
  function renderChart(trend = [], grouping = 'daily') {
    const labels = {
      daily: 'DAILY',
      weekly: 'WEEKLY',
      monthly: 'MONTHLY'
    };

    document.getElementById('trendGroupLabel').textContent =
      labels[grouping] || 'DAILY';

    document.getElementById('trendSubtitle').textContent =
      `Attendance activity grouped by ${grouping} period`;

    if (!trend.length) {
      chartContainer.innerHTML = `
        <div class="trend-empty">
          No attendance activity found for the selected period.
        </div>
      `;
      return;
    }

    const maxTotal = Math.max(
      1,
      ...trend.map(item => Number(item.total) || 0)
    );

    chartContainer.innerHTML = trend.map(item => {
      const total = Number(item.total) || 0;
      const present = Number(item.present) || 0;
      const late = Number(item.late) || 0;

      const barHeight = total > 0
        ? (total / maxTotal) * 100
        : 0;

      const presentHeight = total > 0
        ? (present / total) * 100
        : 0;

      const lateHeight = total > 0
        ? (late / total) * 100
        : 0;

      return `
        <div class="trend-column">

          <span class="trend-total">${total}</span>

          <div class="trend-bar-area">

            <div
              class="trend-bar"
              title="${escapeHTML(item.label)}: ${total} check-ins"
              style="height: ${barHeight}%"
            >

              <div
                class="trend-segment-late"
                style="height: ${lateHeight}%"
              ></div>

              <div
                class="trend-segment-present"
                style="height: ${presentHeight}%"
              ></div>

            </div>

          </div>

          <span class="trend-label">
            ${escapeHTML(item.label)}
          </span>

        </div>
      `;
    }).join('');
  }

  // RENDER ATTENDANCE RECORDS
  function renderRecords(records) {
    visibleRecords = records;

    if (!records.length) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5">
            No attendance records found for this period.
          </td>
        </tr>
      `;
    } else {
      tableBody.innerHTML = records.map(record => {
        const name = escapeHTML(record.full_name);
        const studentNo = escapeHTML(record.student_no);
        const section = escapeHTML(record.section || 'No section');
        const initials = escapeHTML(getInitials(record.full_name));
        const date = escapeHTML(formatDate(record.scanned_at));
        const time = escapeHTML(formatTime(record.scanned_at));

        const status = record.status === 'Present'
          ? 'Present'
          : 'Late';

        const statusClass = status === 'Present'
          ? 'status-present'
          : 'status-late';

        return `
          <tr>

            <td>
              <div class="student-cell">

                <div class="avatar avatar-purple">
                  ${initials}
                </div>

                <span>
                  <strong>${name}</strong>
                  <small>${section}</small>
                </span>

              </div>
            </td>

            <td>${studentNo}</td>
            <td>${date}</td>
            <td>${time}</td>

            <td>
              <span class="status ${statusClass}">
                ${status}
              </span>
            </td>

          </tr>
        `;
      }).join('');
    }

    document.getElementById('reportCount').innerHTML =
      `Showing <strong>${records.length}</strong> attendance records`;
  }

  // SEARCH RECORDS
  function filterRecords() {
    const keyword = (searchInput?.value || '')
      .trim()
      .toLowerCase();

    const filtered = allRecords.filter(record => {
      const searchable = [
        record.full_name,
        record.student_no,
        record.section,
        record.status
      ].join(' ').toLowerCase();

      return searchable.includes(keyword);
    });

    renderRecords(filtered);
  }

  // LOAD REPORT FROM API
  async function loadReport() {
    const filters = {
      start_date: startDate.value,
      end_date: endDate.value,
      status: statusFilter.value,
      group_by: reportType.value
    };

    if (
      filters.start_date &&
      filters.end_date &&
      filters.start_date > filters.end_date
    ) {
      FaceTrack.toast(
        'Start date cannot be later than end date.',
        'error'
      );
      return;
    }

    try {
      generateButton.disabled = true;
      generateButton.textContent = 'Generating...';

      const params = new URLSearchParams();

      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await fetch(
        `${API_BASE}/reports?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();

      allRecords = Array.isArray(result)
        ? result
        : (result.records || []);

      updateSummary(result.summary || {
        total_check_ins: allRecords.length,
        present: allRecords.filter(
          record => record.status === 'Present'
        ).length,
        late: allRecords.filter(
          record => record.status === 'Late'
        ).length,
        unique_students: new Set(
          allRecords.map(record => record.person_id)
        ).size
      });

      renderChart(result.trend || [], result.group_by || filters.group_by);

      filterRecords();

      FaceTrack.toast(
        'Report generated successfully.',
        'success'
      );

    } catch (error) {
      console.error('Report loading error:', error);

      tableBody.innerHTML = `
        <tr>
          <td colspan="5">
            Unable to load report data. Please check the API connection.
          </td>
        </tr>
      `;

      chartContainer.innerHTML = `
        <div class="trend-empty">
          Unable to load attendance trends.
        </div>
      `;

      FaceTrack.toast(
        'Failed to load report data.',
        'error'
      );

    } finally {
      generateButton.disabled = false;
      generateButton.innerHTML =
        'Generate report <span>→</span>';
    }
  }

  // RESET FILTERS
  function resetFilters() {
    const today = new Date();

    startDate.value = localDateString(
      new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      )
    );

    endDate.value = localDateString(today);

    statusFilter.value = '';
    reportType.value = 'daily';
    searchInput.value = '';

    loadReport();
  }

  // EXPORT CSV
  function exportCSV() {
    if (!visibleRecords.length) {
      FaceTrack.toast(
        'There are no records to export.',
        'error'
      );
      return;
    }

    const headers = [
      'Student Name',
      'Student Number',
      'Section',
      'Date',
      'Time In',
      'Status',
      'Face Distance',
      'Session'
    ];

    const rows = visibleRecords.map(record => [
      record.full_name,
      record.student_no,
      record.section,
      formatDate(record.scanned_at),
      formatTime(record.scanned_at),
      record.status,
      record.distance,
      record.session_label
    ]);

    const csv = [headers, ...rows]
      .map(row =>
        row.map(value =>
          `"${String(value ?? '').replace(/"/g, '""')}"`
        ).join(',')
      )
      .join('\r\n');

    const blob = new Blob(
      ['\uFEFF' + csv],
      { type: 'text/csv;charset=utf-8;' }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.href = url;
    link.download =
      `facetrack-report-${localDateString(new Date())}.csv`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);

    FaceTrack.toast(
      'CSV report exported successfully.',
      'success'
    );
  }

  // EVENT LISTENERS
  generateButton?.addEventListener('click', loadReport);

  resetButton?.addEventListener('click', resetFilters);

  exportButton?.addEventListener('click', exportCSV);

  searchInput?.addEventListener('input', filterRecords);

  reportType?.addEventListener('change', loadReport);

  // INITIALIZE REPORTS PAGE
  resetFilters();
});
