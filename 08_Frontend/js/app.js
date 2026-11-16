/* Shared UI helpers used by all FaceTrack pages. */
(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  function toast(message, type = 'info') {
    let node = $('#facetrack-toast');
    if (!node) {
      node = document.createElement('div'); node.id = 'facetrack-toast'; node.setAttribute('role', 'status');
      node.style.cssText = 'position:fixed;right:24px;bottom:24px;z-index:9999;max-width:calc(100vw - 40px);padding:13px 17px;border-radius:12px;background:#17233d;color:white;box-shadow:0 12px 35px #17233d33;font:500 14px/1.45 system-ui;transition:.2s';
      document.body.append(node);
    }
    node.textContent = message; node.style.background = type === 'error' ? '#9f2d3d' : type === 'success' ? '#176b50' : '#17233d';
    node.style.opacity = '1'; clearTimeout(toast.timer); toast.timer = setTimeout(() => node.style.opacity = '0', 3200);
  }
  const read = (key, fallback = []) => { try { return JSON.parse(localStorage.getItem(`facetrack.${key}`)) ?? fallback; } catch { return fallback; } };
  const write = (key, value) => localStorage.setItem(`facetrack.${key}`, JSON.stringify(value));
  const initials = name => String(name || '').trim().split(/\s+/).slice(0, 2).map(x => x[0] || '').join('').toUpperCase() || 'ST';
  const date = value => new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(value ? new Date(value) : new Date());
  document.addEventListener('DOMContentLoaded', () => {
    const current = location.pathname.split('/').pop() || 'index.html';
    $$('.nav-link').forEach(link => link.classList.toggle('active', link.getAttribute('href')?.split('/').pop() === current));
    $$('input[type="search"], .search-input').forEach(input => input.addEventListener('input', () => {
      const tbody = input.closest('.panel')?.querySelector('tbody') || $('tbody'); if (!tbody) return;
      [...tbody.rows].forEach(row => row.hidden = !row.textContent.toLowerCase().includes(input.value.trim().toLowerCase()));
    }));
    $$('a[href="#"]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); toast('This section will be available in a future update.'); }));
    $$('[data-current-date]').forEach(el => el.textContent = date());
  });
  window.FaceTrack = { $, $$, toast, read, write, initials, date };
})();
