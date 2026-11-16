
/* FaceTrack Live Dashboard */
document.addEventListener('DOMContentLoaded', async () => {
  const statsGrid = document.querySelector('.stats-grid');

  if (!statsGrid || !window.FaceTrackAPI) return;

  const statElements = [
    ...statsGrid.querySelectorAll('.stat-value')
  ];

  const showMessage = (message, type = 'info') => {
    let banner = document.querySelector('#dashboard-api-status');

    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'dashboard-api-status';
      banner.setAttribute('role', 'status');

      banner.style.cssText = `
        padding: 12px 16px;
        margin-bottom: 18px;
        border-radius: 10px;
        font-size: 14px;
      `;

      statsGrid.before(banner);
    }

    banner.textContent = message;

    banner.style.background =
      type === 'error' ? '#fff0f0' : '#eef8f2';

    banner.style.color =
      type === 'error' ? '#a12626' : '#176b50';
  };

  const formatNumber = value =>
    Number(value || 0).toLocaleString();

  const formatDate = value => {
    if (!value) return '—';

    const date = new Date(value.replace(' ', 'T'));

    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
  };

  const formatTime = value => {
    if (!value) return '—';

    const date = new Date(value.replace(' ', 'T'));

    return Number.isNaN(date.getTime())
      ? value
      : date.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit'
        });
  };

  function updateRecentAttendance(records) {
    const tbody = document.querySelector(
      '.recent-panel tbody'
    );

    if (!tbody) return;

    tbody.replaceChildren();

    if (!records.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');

      cell.colSpan = 5;
      cell.textContent = 'No attendance records found yet.';
      cell.style.textAlign = 'center';
      cell.style.padding = '24px';

      row.appendChild(cell);
      tbody.appendChild(row);
      return;
    }

    records.slice(0, 5).forEach(record => {
      const row = document.createElement('tr');

      const studentCell = document.createElement('td');
      const studentWrapper = document.createElement('div');
      studentWrapper.className = 'student-cell';

      const avatar = document.createElement('div');
      avatar.className = 'avatar avatar-purple';

      const name = record.full_name || 'Unknown Student';

      avatar.textContent = name
        .split(/\s+/)
        .slice(0, 2)
        .map(part => part[0] || '')
        .join('')
        .toUpperCase();

      const details = document.createElement('span');

      const strong = document.createElement('strong');
      strong.textContent = name;

      const small = document.createElement('small');
      small.textContent = record.section || 'No section';

      details.append(strong, small);
      studentWrapper.append(avatar, details);
      studentCell.appendChild(studentWrapper);

      const idCell = document.createElement('td');
      idCell.textContent = record.student_no || '—';

      const timeCell = document.createElement('td');
      timeCell.textContent = formatTime(record.scanned_at);

      const dateCell = document.createElement('td');
      dateCell.textContent = formatDate(record.scanned_at);

      const statusCell = document.createElement('td');
      const status = document.createElement('span');

      status.textContent = record.status || 'Unknown';
      status.className =
        record.status === 'Late'
          ? 'status status-late'
          : 'status status-present';

      statusCell.appendChild(status);

      row.append(
        studentCell,
        idCell,
        timeCell,
        dateCell,
        statusCell
      );

      tbody.appendChild(row);
    });
  }

  async function loadDashboard() {
    statElements.forEach(element => {
      element.textContent = '...';
    });

    showMessage('Loading live dashboard data...');

    try {
      const [dashboard, attendance] = await Promise.all([
        FaceTrackAPI.getDashboard(),
        FaceTrackAPI.getAttendance()
      ]);

      const values = [
        dashboard.total_students,
        dashboard.present_today,
        dashboard.late_today,
        dashboard.absent_today
      ];

      statElements.forEach((element, index) => {
        element.textContent = formatNumber(values[index]);
      });

      // Update today's breakdown
      const donutTotal = document.querySelector(
        '.donut-center strong'
      );

      if (donutTotal) {
        donutTotal.textContent = formatNumber(
          dashboard.total_students
        );
      }

      const breakdown = document.querySelectorAll(
        '.breakdown-list > div'
      );

      const breakdownValues = [
        dashboard.present_today,
        dashboard.late_today,
        dashboard.absent_today
      ];

      breakdown.forEach((item, index) => {
        const valueElement = item.querySelector('strong');

        if (!valueElement) return;

        const count = Number(breakdownValues[index] || 0);
        const total = Number(dashboard.total_students || 0);
        const percentage = total
          ? ((count / total) * 100).toFixed(1)
          : '0.0';

        valueElement.innerHTML = '';

        const countText = document.createTextNode(
          `${formatNumber(count)} `
        );

        const percentageElement = document.createElement('small');
        percentageElement.textContent = `${percentage}%`;

        valueElement.append(countText, percentageElement);
      });

      // Update recent attendance
      updateRecentAttendance(attendance);

      showMessage('Dashboard successfully connected to the database.');

      // Update page date
      const dateElement = document.querySelector(
        '.page-heading .eyebrow'
      );

      if (dateElement) {
        dateElement.textContent = new Date()
          .toLocaleDateString(undefined, {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric'
          })
          .toUpperCase();
      }

    } catch (error) {
      console.error('[FaceTrack Dashboard]', error);

      showMessage(
        `Unable to load live dashboard data: ${error.message}`,
        'error'
      );

      statElements.forEach(element => {
        element.textContent = '—';
      });
    }
  }

  loadDashboard();
});
