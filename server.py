"""
server.py — Folio Flask dashboard. Run from host project root:
    python3 tools/folio/server.py
"""

import os
import sys
import json

# ---------------------------------------------------------------------------
# Path setup — db.py lives in the same directory as this file
# ---------------------------------------------------------------------------

_FOLIO_DIR = os.path.dirname(os.path.abspath(__file__))
if _FOLIO_DIR not in sys.path:
    sys.path.insert(0, _FOLIO_DIR)

import db
from flask import Flask, request, jsonify, send_from_directory, abort

db.configure(os.getcwd())

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Dashboard HTML — single inline string, no templates directory
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Folio</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:             #f7f6f4;
    --surface:        #ffffff;
    --border:         #e8e6e2;
    --text-primary:   #1a1a1a;
    --text-secondary: #888580;
    --text-muted:     #c0bdb8;
    --sidebar-width:  220px;
    --radius:         6px;
    --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
  }

  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text-primary);
    font-family: var(--font);
    font-size: 14px;
    line-height: 1.5;
  }

  /* ---------- layout ---------- */

  .app {
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    width: var(--sidebar-width);
    flex-shrink: 0;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 20px 0;
    overflow-y: auto;
  }

  .sidebar-project {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    padding: 0 16px 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 8px;
  }

  .sidebar-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    padding: 0 16px 6px;
  }

  .sidebar-tab {
    display: block;
    width: 100%;
    padding: 7px 16px;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    font-family: var(--font);
    font-size: 13px;
    color: var(--text-secondary);
    border-radius: 0;
    transition: background 0.1s;
  }
  .sidebar-tab:hover { background: var(--bg); }
  .sidebar-tab.active {
    color: var(--text-primary);
    font-weight: 500;
    background: var(--bg);
  }

  .main {
    flex: 1;
    overflow-y: auto;
    padding: 24px 28px;
  }

  .main-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
  }

  .main-title {
    font-size: 16px;
    font-weight: 600;
  }

  /* ---------- buttons ---------- */

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 11px;
    border-radius: var(--radius);
    font-family: var(--font);
    font-size: 12px;
    cursor: pointer;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-primary);
    transition: background 0.1s;
    white-space: nowrap;
  }
  .btn:hover { background: var(--bg); }

  .btn-primary {
    background: var(--text-primary);
    color: var(--surface);
    border-color: var(--text-primary);
  }
  .btn-primary:hover { background: #333; }

  .btn-ghost {
    background: none;
    border-color: transparent;
    color: var(--text-secondary);
    padding: 4px 7px;
  }
  .btn-ghost:hover { background: var(--bg); color: var(--text-primary); }

  .btn-danger {
    background: none;
    border-color: transparent;
    color: var(--text-muted);
    padding: 4px 7px;
  }
  .btn-danger:hover { color: #c0392b; background: #fdf0ef; }

  /* ---------- cards ---------- */

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 12px;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px 10px;
    border-bottom: 1px solid var(--border);
  }

  .card-name {
    font-weight: 600;
    font-size: 14px;
    flex: 1;
  }

  .type-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 100px;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    background: var(--bg);
    text-transform: lowercase;
  }

  .status-select {
    font-family: var(--font);
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 100px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text-secondary);
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    padding-right: 18px;
    background-image: url("data:image/svg+xml,%3Csvg width='8' height='5' viewBox='0 0 8 5' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l3 3 3-3' stroke='%23888580' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 5px center;
  }
  .status-select.status-approved    { color: #4a7c59; border-color: #b6d9c3; background-color: #f0f8f3; }
  .status-select.status-finalised   { color: #2c5282; border-color: #b0c8e8; background-color: #ebf2fb; }
  .status-select.status-exploring   { color: var(--text-secondary); }

  .card-meta {
    padding: 8px 16px 0;
    color: var(--text-secondary);
    font-size: 12px;
  }

  /* ---------- variants ---------- */

  .variants-section {
    padding: 10px 16px 14px;
  }

  .variants-heading {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .variant-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 0;
    border-bottom: 1px solid var(--bg);
  }
  .variant-row:last-child { border-bottom: none; }

  .variant-dot {
    font-size: 10px;
    color: var(--text-muted);
    width: 12px;
    flex-shrink: 0;
    text-align: center;
  }
  .variant-dot.is-selected { color: var(--text-primary); }

  .variant-file {
    font-size: 12px;
    font-family: "SF Mono", "Menlo", monospace;
    color: var(--text-primary);
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .variant-label {
    font-size: 11px;
    color: var(--text-secondary);
    min-width: 60px;
  }

  .variant-actions {
    display: flex;
    gap: 2px;
    flex-shrink: 0;
  }

  .card-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px 12px;
  }

  /* ---------- empty state ---------- */

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-secondary);
  }
  .empty-state p { margin-bottom: 16px; }

  /* ---------- modal ---------- */

  .modal-backdrop {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.25);
    z-index: 100;
    align-items: center;
    justify-content: center;
  }
  .modal-backdrop.open { display: flex; }

  .modal {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    width: 440px;
    max-width: calc(100vw - 32px);
    max-height: calc(100vh - 64px);
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px 12px;
    border-bottom: 1px solid var(--border);
  }

  .modal-title { font-size: 14px; font-weight: 600; }

  .modal-close {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 18px;
    color: var(--text-muted);
    line-height: 1;
    padding: 2px 4px;
  }
  .modal-close:hover { color: var(--text-primary); }

  .modal-body { padding: 16px 20px; }

  .form-field {
    margin-bottom: 14px;
  }

  .form-label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 5px;
  }

  .form-input, .form-select, .form-textarea {
    width: 100%;
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-family: var(--font);
    font-size: 13px;
    color: var(--text-primary);
    background: var(--surface);
    transition: border-color 0.15s;
  }
  .form-input:focus, .form-select:focus, .form-textarea:focus {
    outline: none;
    border-color: #aaa;
  }

  .form-textarea {
    resize: vertical;
    min-height: 72px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 20px 16px;
    border-top: 1px solid var(--border);
  }

  /* ---------- system tab ---------- */

  .system-content {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px 28px;
    font-size: 14px;
    line-height: 1.7;
  }

  .system-content h1 { font-size: 20px; margin-bottom: 12px; margin-top: 24px; }
  .system-content h1:first-child { margin-top: 0; }
  .system-content h2 { font-size: 16px; margin-bottom: 8px; margin-top: 20px; }
  .system-content h3 { font-size: 14px; font-weight: 600; margin-bottom: 6px; margin-top: 16px; }
  .system-content p  { margin-bottom: 10px; color: var(--text-secondary); }
  .system-content hr { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
  .system-content table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
  .system-content th, .system-content td {
    text-align: left;
    padding: 7px 12px;
    border: 1px solid var(--border);
    font-size: 13px;
  }
  .system-content th { background: var(--bg); font-weight: 600; }
  .system-content code {
    font-family: "SF Mono", "Menlo", monospace;
    font-size: 12px;
    background: var(--bg);
    padding: 1px 5px;
    border-radius: 3px;
  }
  .system-content pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    overflow-x: auto;
    margin-bottom: 12px;
  }
  .system-content pre code { background: none; padding: 0; }
  .system-content ul, .system-content ol {
    padding-left: 20px;
    margin-bottom: 10px;
    color: var(--text-secondary);
  }
  .system-content li { margin-bottom: 3px; }
</style>
</head>
<body>
<div class="app">

  <!-- Sidebar -->
  <nav class="sidebar">
    <div class="sidebar-project" id="project-name">Folio</div>

    <div class="sidebar-label">Browse</div>
    <button class="sidebar-tab active" data-filter="null" onclick="setFilter(null, this)">All</button>
    <button class="sidebar-tab" data-filter="screen" onclick="setFilter('screen', this)">Screens</button>
    <button class="sidebar-tab" data-filter="layout" onclick="setFilter('layout', this)">Layouts</button>
    <button class="sidebar-tab" data-filter="component" onclick="setFilter('component', this)">Components</button>
    <button class="sidebar-tab" data-filter="flow" onclick="setFilter('flow', this)">Flows</button>

    <div style="margin-top: 20px;">
      <div class="sidebar-label">Tools</div>
      <button class="sidebar-tab" onclick="showSystemTab()">System</button>
    </div>
  </nav>

  <!-- Main -->
  <main class="main">
    <div class="main-header">
      <span class="main-title" id="main-title">All Items</span>
      <button class="btn btn-primary" onclick="openNewItemModal()">+ New item</button>
    </div>
    <div id="items-container"></div>
  </main>

</div>

<!-- Modal -->
<div class="modal-backdrop" id="modal-backdrop" onclick="closeModal(event)">
  <div class="modal" id="modal">
    <div class="modal-header">
      <span class="modal-title" id="modal-title"></span>
      <button class="modal-close" onclick="closeModalDirect()">×</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
    <div class="modal-footer" id="modal-footer"></div>
  </div>
</div>

<script>
// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
  items:        [],
  filter:       null,  // null = all, or type string
  activeTab:    'items',
};

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

window.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.getElementById('project-name');
  const cwd     = window.PROJECT_NAME || document.title;
  titleEl.textContent = cwd;

  loadItems();
});

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

async function loadItems() {
  const url = state.filter ? `/api/items?type=${state.filter}` : '/api/items';
  const res = await fetch(url);
  if (!res.ok) { console.error('Failed to load items', res.status); return; }
  state.items = await res.json();
  renderItems();
}

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

const FILTER_LABELS = {
  null:       'All Items',
  screen:     'Screens',
  layout:     'Layouts',
  component:  'Components',
  flow:       'Flows',
};

function setFilter(type, buttonEl) {
  state.filter    = type;
  state.activeTab = 'items';

  document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
  buttonEl.classList.add('active');
  document.getElementById('main-title').textContent = FILTER_LABELS[type] || 'All Items';

  loadItems();
}

function showSystemTab() {
  state.activeTab = 'system';

  document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('main-title').textContent = 'System';

  renderSystem();
}

// ---------------------------------------------------------------------------
// Rendering — items
// ---------------------------------------------------------------------------

function renderItems() {
  const container = document.getElementById('items-container');
  if (state.items.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No items yet.</p>
        <button class="btn btn-primary" onclick="openNewItemModal()">+ New item</button>
      </div>`;
    return;
  }
  container.innerHTML = state.items.map(renderCard).join('');
}

function renderCard(item) {
  const meta = [item.description, item.usage].filter(Boolean).join(' · ');
  const metaHtml = meta
    ? `<div class="card-meta">${escHtml(meta)}</div>`
    : '';

  const variantsHtml = renderVariants(item);

  return `
  <div class="card" id="card-${item.id}">
    <div class="card-header">
      <span class="card-name">${escHtml(item.name)}</span>
      <span class="type-badge">${escHtml(item.type)}</span>
      <select class="status-select status-${item.status}"
              onchange="updateStatus(${item.id}, this)">
        <option value="exploring"  ${item.status === 'exploring'  ? 'selected' : ''}>exploring</option>
        <option value="approved"   ${item.status === 'approved'   ? 'selected' : ''}>approved</option>
        <option value="finalised"  ${item.status === 'finalised'  ? 'selected' : ''}>finalised</option>
      </select>
      <button class="btn-danger btn" onclick="deleteItem(${item.id})" title="Delete item">✕</button>
    </div>
    ${metaHtml}
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      ${item.selected_file
        ? `<button class="btn btn-ghost" onclick="previewFile('${escAttr(item.selected_file)}')">Preview selected</button>`
        : ''}
    </div>
  </div>`;
}

function renderVariants(item) {
  if (!item.variants || item.variants.length === 0) {
    return `<div class="variants-heading">Variants (0)</div>
            <div style="color: var(--text-muted); font-size: 12px;">No variants yet.</div>`;
  }

  const rows = item.variants.map(v => {
    const isSelected  = v.file === item.selected_file;
    const dotClass    = isSelected ? 'variant-dot is-selected' : 'variant-dot';
    const dotChar     = isSelected ? '●' : '○';
    const label       = v.label ? escHtml(v.label) : '';
    const selectBtn   = isSelected
      ? ''
      : `<button class="btn btn-ghost" onclick="selectVariant(${v.id})">Select</button>`;

    return `
    <div class="variant-row" id="variant-row-${v.id}">
      <span class="${dotClass}">${dotChar}</span>
      <span class="variant-file" title="${escAttr(v.file)}">${escHtml(v.file)}</span>
      <span class="variant-label">${label}</span>
      <div class="variant-actions">
        <button class="btn btn-ghost" onclick="previewFile('${escAttr(v.file)}')">Preview</button>
        ${selectBtn}
        <button class="btn-danger btn" onclick="deleteVariant(${v.id}, ${item.id})" title="Delete variant">✕</button>
      </div>
    </div>`;
  }).join('');

  return `<div class="variants-heading">Variants (${item.variants.length})</div>${rows}`;
}

// ---------------------------------------------------------------------------
// Rendering — system tab
// ---------------------------------------------------------------------------

async function renderSystem() {
  const container = document.getElementById('items-container');
  container.innerHTML = '<div class="system-content"><em style="color:var(--text-muted)">Loading…</em></div>';

  const res = await fetch('/system.md');
  if (!res.ok) {
    container.innerHTML = '<div class="system-content">system.md not found — run <code>init</code> first.</div>';
    return;
  }

  const text = await res.text();
  let html;
  if (typeof marked !== 'undefined') {
    html = marked.parse(text);
  } else {
    html = `<pre style="white-space:pre-wrap">${escHtml(text)}</pre>`;
  }

  container.innerHTML = `<div class="system-content">${html}</div>`;
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function updateStatus(itemId, selectEl) {
  const newStatus = selectEl.value;
  const res = await fetch(`/api/items/${itemId}`, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ status: newStatus }),
  });
  if (!res.ok) { alert('Failed to update status'); selectEl.value = ''; return; }

  // Update class in-place without full re-render
  selectEl.className = `status-select status-${newStatus}`;
}

async function deleteItem(itemId) {
  if (!confirm('Delete this item and all its variants?')) return;
  const res = await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
  if (!res.ok) { alert('Failed to delete item'); return; }
  loadItems();
}

async function selectVariant(variantId) {
  const res = await fetch(`/api/variants/${variantId}/select`, { method: 'PUT' });
  if (!res.ok) { alert('Failed to select variant'); return; }
  loadItems();
}

async function deleteVariant(variantId, itemId) {
  if (!confirm('Delete this variant?')) return;
  const res = await fetch(`/api/variants/${variantId}`, { method: 'DELETE' });
  if (!res.ok) { alert('Failed to delete variant'); return; }
  loadItems();
}

function previewFile(filename) {
  window.open(`/design/${encodeURIComponent(filename)}`, '_blank');
}

// ---------------------------------------------------------------------------
// Modal — new item
// ---------------------------------------------------------------------------

function openNewItemModal() {
  document.getElementById('modal-title').textContent = 'New item';
  document.getElementById('modal-body').innerHTML = `
    <div class="form-field">
      <label class="form-label">Type</label>
      <select class="form-select" id="f-type">
        <option value="screen">screen</option>
        <option value="layout">layout</option>
        <option value="component">component</option>
        <option value="flow">flow</option>
      </select>
    </div>
    <div class="form-field">
      <label class="form-label">Name <span style="color:#c0392b">*</span></label>
      <input class="form-input" id="f-name" type="text" placeholder="e.g. Reading View">
    </div>
    <div class="form-field">
      <label class="form-label">Description</label>
      <textarea class="form-textarea" id="f-description" placeholder="What does this design do?"></textarea>
    </div>
    <div class="form-field">
      <label class="form-label">Usage</label>
      <input class="form-input" id="f-usage" type="text" placeholder="Where / when is this used?">
    </div>
    <div class="form-field">
      <label class="form-label">First variant file (optional)</label>
      <input class="form-input" id="f-file" type="text" placeholder="e.g. reading-view.html">
    </div>`;

  document.getElementById('modal-footer').innerHTML = `
    <button class="btn" onclick="closeModalDirect()">Cancel</button>
    <button class="btn btn-primary" onclick="submitNewItem()">Create</button>`;

  document.getElementById('modal-backdrop').classList.add('open');
  document.getElementById('f-name').focus();
}

async function submitNewItem() {
  const type        = document.getElementById('f-type').value;
  const name        = document.getElementById('f-name').value.trim();
  const description = document.getElementById('f-description').value.trim() || null;
  const usage       = document.getElementById('f-usage').value.trim() || null;
  const file        = document.getElementById('f-file').value.trim() || null;

  if (!name) { alert('Name is required'); return; }

  const res = await fetch('/api/items', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ type, name, description, usage, file }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.error || 'Failed to create item');
    return;
  }

  closeModalDirect();
  loadItems();
}

// ---------------------------------------------------------------------------
// Modal — add variant
// ---------------------------------------------------------------------------

function openAddVariantModal(itemId) {
  document.getElementById('modal-title').textContent = 'Add variant';
  document.getElementById('modal-body').innerHTML = `
    <div class="form-field">
      <label class="form-label">File <span style="color:#c0392b">*</span></label>
      <input class="form-input" id="f-vfile" type="text" placeholder="e.g. reading-view-v2.html">
    </div>
    <div class="form-field">
      <label class="form-label">Label</label>
      <input class="form-input" id="f-vlabel" type="text" placeholder="e.g. Option A">
    </div>
    <div class="form-field">
      <label class="form-label">UI description</label>
      <textarea class="form-textarea" id="f-vuidesc" placeholder="What changed in this variant?"></textarea>
    </div>
    <div class="form-field">
      <label class="form-label">Notes</label>
      <textarea class="form-textarea" id="f-vnotes" placeholder="Implementation notes, concerns, etc."></textarea>
    </div>`;

  document.getElementById('modal-footer').innerHTML = `
    <button class="btn" onclick="closeModalDirect()">Cancel</button>
    <button class="btn btn-primary" onclick="submitNewVariant(${itemId})">Add</button>`;

  document.getElementById('modal-backdrop').classList.add('open');
  document.getElementById('f-vfile').focus();
}

async function submitNewVariant(itemId) {
  const file           = document.getElementById('f-vfile').value.trim();
  const label          = document.getElementById('f-vlabel').value.trim() || null;
  const ui_description = document.getElementById('f-vuidesc').value.trim() || null;
  const notes          = document.getElementById('f-vnotes').value.trim() || null;

  if (!file) { alert('File is required'); return; }

  const res = await fetch(`/api/items/${itemId}/variants`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ file, label, ui_description, notes }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.error || 'Failed to add variant');
    return;
  }

  closeModalDirect();
  loadItems();
}

// ---------------------------------------------------------------------------
// Modal — open / close
// ---------------------------------------------------------------------------

function closeModal(event) {
  if (event.target === document.getElementById('modal-backdrop')) {
    closeModalDirect();
  }
}

function closeModalDirect() {
  document.getElementById('modal-backdrop').classList.remove('open');
  document.getElementById('modal-body').innerHTML   = '';
  document.getElementById('modal-footer').innerHTML = '';
}

// ---------------------------------------------------------------------------
// Keyboard
// ---------------------------------------------------------------------------

window.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModalDirect();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escAttr(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
</script>
<script>
  window.PROJECT_NAME = (function() {
    try {
      const parts = window.location.hostname === 'localhost'
        ? ['Folio']
        : window.location.pathname.split('/').filter(Boolean);
      return document.title || 'Folio';
    } catch(_) { return 'Folio'; }
  })();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

def _item_not_found(item_id: int):
    return jsonify({"error": f"Item {item_id} not found"}), 404


def _variant_not_found(variant_id: int):
    return jsonify({"error": f"Variant {variant_id} not found"}), 404


@app.route("/")
def route_dashboard():
    return DASHBOARD_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/design/<path:filename>")
def route_design_file(filename: str):
    assert filename, "filename must not be empty"
    return send_from_directory(db.DESIGN_DIR, filename)


@app.route("/screenshots/<path:filename>")
def route_screenshot_file(filename: str):
    assert filename, "filename must not be empty"
    return send_from_directory(db.SCREENSHOTS_DIR, filename)


@app.route("/system.md")
def route_system_md():
    if not os.path.exists(db.SYSTEM_MD_PATH):
        abort(404)
    with open(db.SYSTEM_MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/api/items", methods=["GET"])
def api_get_items():
    type_filter = request.args.get("type") or None
    if type_filter is not None and type_filter not in {"screen", "layout", "component", "flow"}:
        return jsonify({"error": f"Invalid type: {type_filter!r}"}), 400
    items = db.list_items(type_filter=type_filter)
    return jsonify(items)


@app.route("/api/items", methods=["POST"])
def api_create_item():
    data = request.get_json(force=True, silent=True) or {}
    try:
        item = db.create_item(
            type=data.get("type", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            usage=data.get("usage"),
        )
    except (ValueError, AssertionError) as exc:
        return jsonify({"error": str(exc)}), 400

    # Optionally create first variant if "file" was provided
    first_file = data.get("file")
    if first_file:
        try:
            variant = db.create_variant(item_id=item["id"], file=first_file, label="v1")
            db.select_variant(variant["id"])
            # Reload item to include variant + selected_file
            item = db.get_item(item["id"])
        except (ValueError, AssertionError) as exc:
            return jsonify({"error": str(exc)}), 400

    return jsonify(item), 201


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def api_update_item(item_id: int):
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No fields provided"}), 400
    try:
        item = db.update_item(item_id, **data)
    except (ValueError, AssertionError) as exc:
        return jsonify({"error": str(exc)}), 400
    if item is None:
        return _item_not_found(item_id)
    return jsonify(item)


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def api_delete_item(item_id: int):
    deleted = db.delete_item(item_id)
    if not deleted:
        return _item_not_found(item_id)
    return jsonify({"deleted": True})


@app.route("/api/items/<int:item_id>/variants", methods=["POST"])
def api_create_variant(item_id: int):
    data = request.get_json(force=True, silent=True) or {}
    try:
        variant = db.create_variant(
            item_id=item_id,
            file=data.get("file", ""),
            label=data.get("label"),
            ui_description=data.get("ui_description"),
            notes=data.get("notes"),
        )
    except (ValueError, AssertionError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(variant), 201


@app.route("/api/variants/<int:variant_id>/select", methods=["PUT"])
def api_select_variant(variant_id: int):
    item = db.select_variant(variant_id)
    if item is None:
        return _variant_not_found(variant_id)
    return jsonify(item)


@app.route("/api/variants/<int:variant_id>", methods=["DELETE"])
def api_delete_variant(variant_id: int):
    deleted = db.delete_variant(variant_id)
    if not deleted:
        return _variant_not_found(variant_id)
    return jsonify({"deleted": True})


@app.route("/variants/<int:variant_id>/screenshot", methods=["POST"])
def route_upload_screenshot(variant_id: int):
    if "file" not in request.files:
        return jsonify({"error": "No file in request"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "Empty filename"}), 400

    os.makedirs(db.SCREENSHOTS_DIR, exist_ok=True)

    safe_name    = f"variant_{variant_id}.png"
    save_path    = os.path.join(db.SCREENSHOTS_DIR, safe_name)
    relative_path = safe_name

    uploaded.save(save_path)
    updated = db.update_variant_screenshot(variant_id, relative_path)
    if not updated:
        return _variant_not_found(variant_id)

    return jsonify({"screenshot": relative_path})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5555
    print(f"Folio dashboard → http://{host}:{port}")
    print(f"  DB:      {db.DB_PATH}")
    print(f"  Design:  {db.DESIGN_DIR}")
    print(f"  System:  {db.SYSTEM_MD_PATH}")
    app.run(host=host, port=port, debug=True)
