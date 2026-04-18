"""
server.py — Folio dashboard. Run from host project root:
    python3 tools/folio/server.py
"""

import atexit
import json
import mimetypes
import os
import re
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

_PID_FILE = Path.home() / ".folio" / "server.pid"


def _write_pid() -> None:
    _PID_FILE.write_text(str(os.getpid()))


def _remove_pid() -> None:
    _PID_FILE.unlink(missing_ok=True)


def _handle_signal(sig, frame) -> None:
    _remove_pid()
    sys.exit(0)

# ---------------------------------------------------------------------------
# Path setup — db.py lives in the folio lib directory
# ---------------------------------------------------------------------------

_FOLIO_LIB = str(Path.home() / ".folio" / "lib")
if _FOLIO_LIB not in sys.path:
    sys.path.insert(0, _FOLIO_LIB)

import db

db.configure(Path.cwd())

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
    --bg:             #131518;
    --surface:        #1b1e24;
    --border:         #2a2f3a;
    --text-primary:   #ede6d8;
    --text-secondary: #a8a8bc;
    --text-muted:     #68687c;
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
  .btn-primary:hover { background: #d4c4a0; }

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
  .btn-danger:hover { color: #b07878; background: #231820; }

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
  .status-select.status-approved    { color: #6aaa84; border-color: #28443a; background-color: #151d1a; }
  .status-select.status-finalised   { color: #6890b8; border-color: #243050; background-color: #141a28; }
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

  /* ---------- used-in / linked-screens ---------- */

  .linked-section {
    padding: 8px 16px 0;
  }

  .linked-heading {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .linked-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 8px;
  }

  .linked-tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 100px;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    background: var(--bg);
  }

  /* ---------- flow screen tree ---------- */

  .screen-tree {
    padding: 8px 16px 0;
  }

  .screen-tree-heading {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .screen-tree-list {
    list-style: none;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }

  .screen-tree-list li {
    padding: 2px 0;
  }

  .screen-tree-children {
    list-style: none;
    padding-left: 16px;
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
    border-color: #7a6050;
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

  /* ---------- flow tree ---------- */
  .flow-tree-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
  .flow-tree-zoom { display: flex; gap: 4px; }
  .flow-tree-zoom button {
    width: 28px; height: 28px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-size: 14px;
    cursor: pointer;
    font-family: var(--font);
    display: flex; align-items: center; justify-content: center;
  }
  .flow-tree-zoom button:hover { background: var(--bg); }

  .flow-tree-view {
    position: relative;
    width: 100%;
    height: calc(100vh - 120px);
    overflow: hidden;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: grab;
    user-select: none;
  }
  .flow-tree-view.grabbing { cursor: grabbing; }

  .flow-tree-canvas {
    position: absolute;
    top: 0; left: 0;
    transform-origin: 0 0;
  }

  .flow-tree-svg {
    position: absolute;
    top: 0; left: 0;
    pointer-events: none;
    overflow: visible;
  }

  .flow-node {
    position: absolute;
    width: 200px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }
  .flow-node.status-approved  { border-color: #38604a; }
  .flow-node.status-finalised { border-color: #2e5070; }

  .flow-node-thumb {
    position: relative;
    width: 200px;
    height: 120px;
    overflow: hidden;
    background: #0e1014;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
  }
  .flow-node-thumb-scale {
    width: 800px;
    height: 480px;
    transform: scale(0.25);
    transform-origin: 0 0;
    margin-right: -600px;
    margin-bottom: -360px;
    pointer-events: none;
  }
  .flow-node-thumb-scale iframe {
    width: 800px;
    height: 480px;
    border: none;
    display: block;
  }
  .flow-node-thumb-open {
    position: absolute;
    top: 6px; right: 6px;
    background: rgba(20,22,28,0.75);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-secondary);
    font-size: 10px;
    padding: 2px 6px;
    cursor: pointer;
    font-family: var(--font);
    z-index: 1;
  }
  .flow-node-thumb-open:hover { color: var(--text-primary); }

  .flow-node-info {
    padding: 7px 10px 9px;
  }
  .flow-node-name {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 4px;
  }
  .flow-node-status {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 100px;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    background: var(--bg);
    display: inline-block;
    text-transform: lowercase;
  }
  .flow-node-status.status-approved  { color: #6aaa84; border-color: #28443a; background: #151d1a; }
  .flow-node-status.status-finalised { color: #6890b8; border-color: #243050; background: #141a28; }

  #preview-drawer.open { right: 0; }
</style>
</head>
<body>
<div class="app">

  <!-- Sidebar -->
  <nav class="sidebar">
    <div class="sidebar-project" id="project-name">Folio</div>

    <div class="sidebar-label">Browse</div>
    <button class="sidebar-tab active" onclick="setSection('screens', this)">Screens</button>
    <button class="sidebar-tab" onclick="setSection('components', this)">Components</button>
    <button class="sidebar-tab" onclick="setSection('flows', this)">Flows</button>

    <div style="margin-top: 20px;">
      <div class="sidebar-label">Tools</div>
      <button class="sidebar-tab" onclick="showSystemTab()">System</button>
    </div>
  </nav>

  <!-- Main -->
  <main class="main">
    <div class="main-header">
      <span class="main-title" id="main-title">Screens</span>
      <button class="btn btn-primary" id="new-item-btn" onclick="openNewItemModal()">+ New screen</button>
    </div>
    <div id="items-container"></div>
  </main>

</div>

<!-- Preview drawer -->
<div id="preview-drawer" style="
  position:fixed; top:0; right:-440px; width:420px; height:100vh;
  background:var(--surface); border-left:1px solid var(--border);
  display:flex; flex-direction:column; z-index:200;
  transition:right 0.22s ease; box-shadow:-4px 0 24px rgba(0,0,0,0.3);
">
  <div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--border);flex-shrink:0">
    <span id="preview-drawer-title" style="font-size:13px;font-weight:600;color:var(--text-primary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
    <button id="preview-newtab-btn" class="btn" onclick="previewNewTab()" title="Open in new tab">↗</button>
    <button class="btn" onclick="closePreviewDrawer()" title="Close">✕</button>
  </div>
  <iframe id="preview-iframe" src="" style="flex:1;border:none;background:#fff"></iframe>
</div>
<div id="preview-backdrop" onclick="closePreviewDrawer()" style="display:none;position:fixed;inset:0;z-index:199"></div>

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
  section: 'screens',  // 'screens' | 'components' | 'flows'
  items: [],
  treeFlowId: null,
};

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

window.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.getElementById('project-name');
  titleEl.textContent = window.PROJECT_NAME || 'Folio';
  loadSection();
});

// ---------------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------------

async function loadSection() {
  const res = await fetch(`/api/${state.section}`);
  if (!res.ok) { console.error('Failed to load section', res.status); return; }
  state.items = await res.json();
  renderSection();
}

// ---------------------------------------------------------------------------
// Section switching
// ---------------------------------------------------------------------------

function setSection(section, btn) {
  state.section = section;
  document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const titles = { screens: 'Screens', components: 'Components', flows: 'Flows' };
  document.getElementById('main-title').textContent = titles[section];

  const singular = section.slice(0, -1);
  document.getElementById('new-item-btn').textContent = `+ New ${singular}`;

  loadSection();
}

function showSystemTab() {
  document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('main-title').textContent = 'System';
  renderSystem();
}

// ---------------------------------------------------------------------------
// Rendering — dispatch
// ---------------------------------------------------------------------------

function renderSection() {
  if (state.section === 'screens')    { renderScreens();    return; }
  if (state.section === 'components') { renderComponents(); return; }
  if (state.section === 'flows')      { renderFlows();      return; }
}

// ---------------------------------------------------------------------------
// Rendering — screens
// ---------------------------------------------------------------------------

function renderScreens() {
  const container = document.getElementById('items-container');
  if (state.items.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No screens yet.</p>
        <button class="btn btn-primary" onclick="openNewItemModal()">+ New screen</button>
      </div>`;
    return;
  }
  container.innerHTML = state.items.map(renderScreenCard).join('');
}

function renderScreenCard(item) {
  const meta = [item.description, item.usage].filter(Boolean).join(' · ');
  const metaHtml = meta
    ? `<div class="card-meta">${escHtml(meta)}</div>`
    : '';

  const parentHtml = item.parent_id
    ? `<div class="card-meta" style="color:var(--text-muted);font-size:11px;">&#8627; child of #${item.parent_id}</div>`
    : '';

  const variantsHtml = renderVariants(item, 'screen');

  const selectedFile = item.selected_file || null;
  const previewBtn = selectedFile
    ? `<button class="btn btn-ghost" onclick="previewFile('${escAttr(selectedFile)}')">Preview selected</button>`
    : '';

  return `
  <div class="card" id="card-${item.id}">
    <div class="card-header">
      <span class="card-name">${escHtml(item.name)}</span>
      <select class="status-select status-${item.status}"
              onchange="updateStatus(${item.id}, this)">
        <option value="exploring"  ${item.status === 'exploring'  ? 'selected' : ''}>exploring</option>
        <option value="approved"   ${item.status === 'approved'   ? 'selected' : ''}>approved</option>
        <option value="finalised"  ${item.status === 'finalised'  ? 'selected' : ''}>finalised</option>
      </select>
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    ${parentHtml}
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      ${previewBtn}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Rendering — components
// ---------------------------------------------------------------------------

function renderComponents() {
  const container = document.getElementById('items-container');
  if (state.items.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No components yet.</p>
        <button class="btn btn-primary" onclick="openNewItemModal()">+ New component</button>
      </div>`;
    return;
  }
  container.innerHTML = state.items.map(renderComponentCard).join('');
}

function renderComponentCard(item) {
  const meta = [item.description, item.usage].filter(Boolean).join(' · ');
  const metaHtml = meta
    ? `<div class="card-meta">${escHtml(meta)}</div>`
    : '';

  const usedIn = item.used_in || [];
  const usedInHtml = usedIn.length > 0
    ? `<div class="linked-tags">${usedIn.map(s => `<span class="linked-tag">${escHtml(s.name)}</span>`).join('')}</div>`
    : `<div style="color:var(--text-muted);font-size:12px;margin-bottom:8px;">Not linked to any screen</div>`;

  const variantsHtml = renderVariants(item, 'component');

  const selectedFile = item.selected_file || null;
  const previewBtn = selectedFile
    ? `<button class="btn btn-ghost" onclick="previewFile('${escAttr(selectedFile)}')">Preview selected</button>`
    : '';

  return `
  <div class="card" id="card-${item.id}">
    <div class="card-header">
      <span class="card-name">${escHtml(item.name)}</span>
      <select class="status-select status-${item.status}"
              onchange="updateStatus(${item.id}, this)">
        <option value="exploring"  ${item.status === 'exploring'  ? 'selected' : ''}>exploring</option>
        <option value="approved"   ${item.status === 'approved'   ? 'selected' : ''}>approved</option>
        <option value="finalised"  ${item.status === 'finalised'  ? 'selected' : ''}>finalised</option>
      </select>
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    <div class="linked-section">
      <div class="linked-heading">Used in</div>
      ${usedInHtml}
    </div>
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      <button class="btn" onclick="openLinkScreenModal(${item.id})">+ Link screen</button>
      ${previewBtn}
    </div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Rendering — flows
// ---------------------------------------------------------------------------

function renderFlows() {
  const container = document.getElementById('items-container');
  if (state.items.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No flows yet.</p>
        <button class="btn btn-primary" onclick="openNewItemModal()">+ New flow</button>
      </div>`;
    return;
  }
  container.innerHTML = state.items.map(renderFlowCard).join('');
}

function renderFlowCard(item) {
  const meta = [item.description, item.usage].filter(Boolean).join(' · ');
  const metaHtml = meta
    ? `<div class="card-meta">${escHtml(meta)}</div>`
    : '';

  const screens = item.screens || [];
  const screenTreeHtml = renderFlowScreenTree(screens);

  const variantsHtml = renderVariants(item, 'flow');

  const selectedFile = item.selected_file || null;
  const previewBtn = selectedFile
    ? `<button class="btn btn-ghost" onclick="previewFile('${escAttr(selectedFile)}')">Preview selected</button>`
    : '';

  const screensJson = JSON.stringify(screens).replace(/'/g, '&#39;');
  const viewTreeBtn = screens.length > 0
    ? `<button class="btn" onclick="openFlowTree(${item.id}, '${escAttr(item.name)}', JSON.parse(this.dataset.screens))" data-screens="${escAttr(JSON.stringify(screens))}">View tree →</button>`
    : '';

  return `
  <div class="card" id="card-${item.id}">
    <div class="card-header">
      <span class="card-name" style="cursor:pointer;text-decoration:underline dotted"
            onclick="openFlowTree(${item.id}, '${escAttr(item.name)}', JSON.parse(this.dataset.screens))"
            data-screens="${escAttr(JSON.stringify(screens))}">${escHtml(item.name)}</span>
      <select class="status-select status-${item.status}"
              onchange="updateStatus(${item.id}, this)">
        <option value="exploring"  ${item.status === 'exploring'  ? 'selected' : ''}>exploring</option>
        <option value="approved"   ${item.status === 'approved'   ? 'selected' : ''}>approved</option>
        <option value="finalised"  ${item.status === 'finalised'  ? 'selected' : ''}>finalised</option>
      </select>
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    ${screenTreeHtml}
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      <button class="btn" onclick="openLinkScreenModal(${item.id})">+ Link screen</button>
      ${viewTreeBtn}
      ${previewBtn}
    </div>
  </div>`;
}

function renderFlowScreenTree(screens) {
  if (screens.length === 0) {
    return '';
  }

  // Build set of IDs in this flow for root detection.
  const linkedIds = new Set(screens.map(s => s.id));

  // Group children by parent.
  const childrenByParent = {};
  const roots = [];

  for (const screen of screens) {
    if (!screen.parent_id || !linkedIds.has(screen.parent_id)) {
      roots.push(screen);
    } else {
      if (!childrenByParent[screen.parent_id]) {
        childrenByParent[screen.parent_id] = [];
      }
      childrenByParent[screen.parent_id].push(screen);
    }
  }

  function renderNode(screen) {
    const children = childrenByParent[screen.id] || [];
    const childrenHtml = children.length > 0
      ? `<ul class="screen-tree-children">${children.map(renderNode).join('')}</ul>`
      : '';
    return `<li>&#11044; ${escHtml(screen.name)}${childrenHtml}</li>`;
  }

  const listHtml = roots.map(renderNode).join('');

  return `
  <div class="screen-tree">
    <div class="screen-tree-heading">Screens</div>
    <ul class="screen-tree-list">${listHtml}</ul>
  </div>`;
}

// ---------------------------------------------------------------------------
// Rendering — variants (shared)
// ---------------------------------------------------------------------------

function renderVariants(item, entityType) {
  const variants = item.variants || [];

  if (variants.length === 0) {
    return `<div class="variants-heading">Variants (0)</div>
            <div style="color: var(--text-muted); font-size: 12px;">No variants yet.</div>`;
  }

  const rows = variants.map(v => {
    const isSelected = v.file === item.selected_file;
    const dotClass   = isSelected ? 'variant-dot is-selected' : 'variant-dot';
    const dotChar    = isSelected ? '&#11044;' : '&#9900;';
    const label      = v.label ? escHtml(v.label) : '';
    const selectBtn  = isSelected
      ? ''
      : `<button class="btn btn-ghost" onclick="selectVariant(${v.id}, '${entityType}')">Select</button>`;

    return `
    <div class="variant-row" id="variant-row-${v.id}">
      <span class="${dotClass}">${dotChar}</span>
      <span class="variant-file" title="${escAttr(v.file)}">${escHtml(v.file)}</span>
      <span class="variant-label">${label}</span>
      <div class="variant-actions">
        <button class="btn btn-ghost" onclick="previewFile('${escAttr(v.file)}')">Preview</button>
        ${selectBtn}
        <button class="btn-danger btn" onclick="deleteVariant(${v.id}, '${entityType}')" title="Delete variant">&#x2715;</button>
      </div>
    </div>`;
  }).join('');

  return `<div class="variants-heading">Variants (${variants.length})</div>${rows}`;
}

// ---------------------------------------------------------------------------
// Rendering — system tab
// ---------------------------------------------------------------------------

async function renderSystem() {
  const container = document.getElementById('items-container');
  container.innerHTML = '<div class="system-content"><em style="color:var(--text-muted)">Loading&#8230;</em></div>';

  const res = await fetch('/system.md');
  if (!res.ok) {
    container.innerHTML = '<div class="system-content">system.md not found &#8212; run <code>init</code> first.</div>';
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
// API calls — entity actions
// ---------------------------------------------------------------------------

async function updateStatus(entityId, selectEl) {
  const newStatus = selectEl.value;
  const res = await fetch(`/api/${state.section}/${entityId}`, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ status: newStatus }),
  });
  if (!res.ok) { alert('Failed to update status'); selectEl.value = ''; return; }
  selectEl.className = `status-select status-${newStatus}`;
}

async function deleteEntity(entityId) {
  if (!confirm('Delete this item and all its variants?')) return;
  const res = await fetch(`/api/${state.section}/${entityId}`, { method: 'DELETE' });
  if (!res.ok) { alert('Failed to delete'); return; }
  loadSection();
}

// ---------------------------------------------------------------------------
// API calls — variant actions
// ---------------------------------------------------------------------------

async function selectVariant(variantId, entityType) {
  const prefix = entityType === 'screen'    ? 'screen-variants'
               : entityType === 'component' ? 'component-variants'
               : 'flow-variants';
  const res = await fetch(`/api/${prefix}/${variantId}/select`, { method: 'PUT' });
  if (!res.ok) { alert('Failed to select variant'); return; }
  loadSection();
}

async function deleteVariant(variantId, entityType) {
  if (!confirm('Delete this variant?')) return;
  const prefix = entityType === 'screen'    ? 'screen-variants'
               : entityType === 'component' ? 'component-variants'
               : 'flow-variants';
  const res = await fetch(`/api/${prefix}/${variantId}`, { method: 'DELETE' });
  if (!res.ok) { alert('Failed to delete variant'); return; }
  loadSection();
}

let _previewCurrentFile = null;

function previewFile(filename) {
  _previewCurrentFile = filename;
  const drawer = document.getElementById('preview-drawer');
  const iframe = document.getElementById('preview-iframe');
  const title  = document.getElementById('preview-drawer-title');
  iframe.src = `/design/${encodeURIComponent(filename)}`;
  title.textContent = filename;
  drawer.style.right = '0';
  document.getElementById('preview-backdrop').style.display = 'block';
}

function closePreviewDrawer() {
  const drawer = document.getElementById('preview-drawer');
  drawer.style.right = '-440px';
  document.getElementById('preview-backdrop').style.display = 'none';
  setTimeout(() => { document.getElementById('preview-iframe').src = ''; }, 250);
  _previewCurrentFile = null;
}

function previewNewTab() {
  if (_previewCurrentFile) {
    window.open(`/design/${encodeURIComponent(_previewCurrentFile)}`, '_blank');
  }
}

// ---------------------------------------------------------------------------
// Modal — new item
// ---------------------------------------------------------------------------

function openNewItemModal() {
  const singular = state.section.slice(0, -1);
  document.getElementById('modal-title').textContent = `New ${singular}`;

  const showFile = state.section !== 'flows';
  const fileField = showFile ? `
    <div class="form-field">
      <label class="form-label">First variant file (optional)</label>
      <input class="form-input" id="f-file" type="text" placeholder="e.g. reading-view.html">
    </div>` : '';

  document.getElementById('modal-body').innerHTML = `
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
    ${fileField}`;

  document.getElementById('modal-footer').innerHTML = `
    <button class="btn" onclick="closeModalDirect()">Cancel</button>
    <button class="btn btn-primary" onclick="submitNewItem()">Create</button>`;

  document.getElementById('modal-backdrop').classList.add('open');
  document.getElementById('f-name').focus();
}

async function submitNewItem() {
  const name        = document.getElementById('f-name').value.trim();
  const description = document.getElementById('f-description').value.trim() || null;
  const usage       = document.getElementById('f-usage').value.trim() || null;
  const fileEl      = document.getElementById('f-file');
  const file        = fileEl ? fileEl.value.trim() || null : null;

  if (!name) { alert('Name is required'); return; }

  const res = await fetch(`/api/${state.section}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ name, description, usage, file }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.error || 'Failed to create');
    return;
  }

  closeModalDirect();
  loadSection();
}

// ---------------------------------------------------------------------------
// Modal — add variant
// ---------------------------------------------------------------------------

function openAddVariantModal(entityId) {
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
    <button class="btn btn-primary" onclick="submitNewVariant(${entityId})">Add</button>`;

  document.getElementById('modal-backdrop').classList.add('open');
  document.getElementById('f-vfile').focus();
}

async function submitNewVariant(entityId) {
  const file           = document.getElementById('f-vfile').value.trim();
  const label          = document.getElementById('f-vlabel').value.trim() || null;
  const ui_description = document.getElementById('f-vuidesc').value.trim() || null;
  const notes          = document.getElementById('f-vnotes').value.trim() || null;

  if (!file) { alert('File is required'); return; }

  const res = await fetch(`/api/${state.section}/${entityId}/variants`, {
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
  loadSection();
}

// ---------------------------------------------------------------------------
// Modal — link screen
// ---------------------------------------------------------------------------

function openLinkScreenModal(entityId) {
  document.getElementById('modal-title').textContent = 'Link screen';
  document.getElementById('modal-body').innerHTML = `
    <div class="form-field">
      <label class="form-label">Screen ID <span style="color:#c0392b">*</span></label>
      <input class="form-input" id="f-screen-id" type="number" placeholder="e.g. 3">
    </div>`;

  document.getElementById('modal-footer').innerHTML = `
    <button class="btn" onclick="closeModalDirect()">Cancel</button>
    <button class="btn btn-primary" onclick="submitLinkScreen(${entityId})">Link</button>`;

  document.getElementById('modal-backdrop').classList.add('open');
  document.getElementById('f-screen-id').focus();
}

async function submitLinkScreen(entityId) {
  const screenIdRaw = document.getElementById('f-screen-id').value.trim();
  const screen_id   = parseInt(screenIdRaw, 10);

  if (!screenIdRaw || isNaN(screen_id) || screen_id <= 0) {
    alert('A valid screen ID is required');
    return;
  }

  const res = await fetch(`/api/${state.section}/${entityId}/link-screen`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ screen_id }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.error || 'Failed to link screen');
    return;
  }

  closeModalDirect();
  loadSection();
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
  if (e.key === 'Escape') { closePreviewDrawer(); closeModalDirect(); }
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Flow tree view
// ---------------------------------------------------------------------------

function openFlowTree(flowId, flowName, screens) {
  state.treeFlowId = flowId;

  // Layout constants — thumb 200×120, info ~45px → node 165px tall
  const NW = 200, NH = 165, HGAP = 48, VGAP = 72;
  const linkedIds = new Set(screens.map(s => s.id));

  // Build child map
  const kids = {};
  for (const s of screens) { kids[s.id] = []; }
  for (const s of screens) {
    if (s.parent_id && linkedIds.has(s.parent_id)) {
      kids[s.parent_id].push(s);
    }
  }
  const roots = screens.filter(s => !s.parent_id || !linkedIds.has(s.parent_id));

  // Recursive subtree layout — returns subtree width
  const pos = {};
  let maxX = 0;
  function layout(node, depth, x0) {
    const children = kids[node.id] || [];
    if (!children.length) {
      pos[node.id] = { x: x0, y: depth * (NH + VGAP) };
      maxX = Math.max(maxX, x0);
      return NW;
    }
    let cx = x0, total = 0;
    for (const c of children) {
      const sw = layout(c, depth + 1, cx);
      cx += sw + HGAP;
      total += sw + HGAP;
    }
    total -= HGAP;
    const mid = (pos[children[0].id].x + pos[children[children.length - 1].id].x) / 2;
    pos[node.id] = { x: mid, y: depth * (NH + VGAP) };
    maxX = Math.max(maxX, mid);
    return Math.max(total, NW);
  }
  let cx0 = 0;
  for (const r of roots) { cx0 += layout(r, 0, cx0) + HGAP; }

  // SVG bezier arrows
  let arrows = '';
  for (const s of screens) {
    if (s.parent_id && linkedIds.has(s.parent_id) && pos[s.parent_id] && pos[s.id]) {
      const x1 = pos[s.parent_id].x + NW / 2, y1 = pos[s.parent_id].y + NH;
      const x2 = pos[s.id].x + NW / 2,        y2 = pos[s.id].y;
      const my = (y1 + y2) / 2;
      arrows += `<path d="M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2 - 7}" fill="none" stroke="#3a4458" stroke-width="1.5" marker-end="url(#arr)"/>`;
    }
  }

  // Node HTML — negative-margin trick collapses scaled iframe layout footprint
  let nodes = '';
  for (const s of screens) {
    if (!pos[s.id]) { continue; }
    const { x, y } = pos[s.id];
    const sc = `status-${s.status || 'exploring'}`;
    const thumb = s.selected_file
      ? `<div class="flow-node-thumb" onclick="event.stopPropagation();previewFile('${escAttr(s.selected_file)}')">
           <div class="flow-node-thumb-scale">
             <iframe src="/design/${encodeURIComponent(s.selected_file)}" loading="lazy"></iframe>
           </div>
           <button class="flow-node-thumb-open" onclick="event.stopPropagation();window.open('/design/${encodeURIComponent(s.selected_file)}','_blank')">↗</button>
         </div>`
      : `<div class="flow-node-thumb" style="cursor:default;display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-size:11px">No file</div>`;
    nodes += `
      <div class="flow-node ${sc}" style="left:${x}px;top:${y}px">
        ${thumb}
        <div class="flow-node-info">
          <div class="flow-node-name" title="${escAttr(s.name)}">${escHtml(s.name)}</div>
          <span class="flow-node-status ${sc}">${escHtml(s.status || 'exploring')}</span>
        </div>
      </div>`;
  }

  const posVals = Object.values(pos);
  const canvasW = maxX + NW + 60;
  const canvasH = (posVals.length ? posVals.reduce((m, p) => Math.max(m, p.y), 0) : 0) + NH + 60;

  document.getElementById('items-container').innerHTML = `
    <div class="flow-tree-controls">
      <button class="btn" onclick="closeFlowTree()">&#8592; Flows</button>
      <span style="font-size:13px;font-weight:600;color:var(--text-primary)">${escHtml(flowName)}</span>
      <div style="flex:1"></div>
      <div class="flow-tree-zoom">
        <button onclick="zoomTree(-0.1)">&#8722;</button>
        <button onclick="zoomTree(0.1)">+</button>
        <button onclick="resetZoom()">&#8635;</button>
      </div>
    </div>
    <div class="flow-tree-view" id="ftv">
      <div class="flow-tree-canvas" id="ftc" style="width:${canvasW}px;height:${canvasH}px">
        <svg class="flow-tree-svg" id="fts" width="${canvasW}" height="${canvasH}">
          <defs>
            <marker id="arr" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto-start-reverse">
              <polygon points="0 0,10 3.5,0 7" fill="#3a4458"/>
            </marker>
          </defs>
          ${arrows}
        </svg>
        ${nodes}
      </div>
    </div>`;

  let scale = 1, panX = 20, panY = 20, dragging = false, lx = 0, ly = 0;
  const view = document.getElementById('ftv');
  const canvas = document.getElementById('ftc');

  function applyT() {
    canvas.style.transform = `translate(${panX}px,${panY}px) scale(${scale})`;
  }
  applyT();

  view.addEventListener('mousedown', e => {
    dragging = true; lx = e.clientX; ly = e.clientY;
    view.classList.add('grabbing');
  });
  window.addEventListener('mousemove', e => {
    if (!dragging) { return; }
    panX += e.clientX - lx; panY += e.clientY - ly;
    lx = e.clientX; ly = e.clientY;
    applyT();
  });
  window.addEventListener('mouseup', () => { dragging = false; view.classList.remove('grabbing'); });
  view.addEventListener('wheel', e => {
    e.preventDefault();
    scale = Math.max(0.3, Math.min(2.5, scale + (e.deltaY > 0 ? -0.08 : 0.08)));
    applyT();
  }, { passive: false });

  window._treeZoom  = { get scale() { return scale; }, set scale(v) { scale = v; applyT(); } };
  window._treeReset = () => { scale = 1; panX = 20; panY = 20; applyT(); };
}

function zoomTree(delta) {
  if (!window._treeZoom) { return; }
  window._treeZoom.scale = Math.max(0.3, Math.min(2.5, window._treeZoom.scale + delta));
}

function resetZoom() {
  if (window._treeReset) { window._treeReset(); }
}

function closeFlowTree() {
  state.treeFlowId = null;
  loadSection();
}

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
# Request handler
# ---------------------------------------------------------------------------

# Compiled route patterns for parameterised paths.
_RE_DESIGN      = re.compile(r"^/design/(.+)$")
_RE_SCREENSHOTS = re.compile(r"^/screenshots/(.+)$")
_RE_SCREENSHOT  = re.compile(r"^/variants/(\d+)/screenshot$")

_RE_SCREENS        = re.compile(r"^/api/screens$")
_RE_SCREEN         = re.compile(r"^/api/screens/(\d+)$")
_RE_SCREEN_PARENT  = re.compile(r"^/api/screens/(\d+)/parent$")
_RE_SCREEN_VARS    = re.compile(r"^/api/screens/(\d+)/variants$")
_RE_SCREEN_VAR_SEL = re.compile(r"^/api/screen-variants/(\d+)/select$")
_RE_SCREEN_VAR     = re.compile(r"^/api/screen-variants/(\d+)$")

_RE_COMPONENTS        = re.compile(r"^/api/components$")
_RE_COMPONENT         = re.compile(r"^/api/components/(\d+)$")
_RE_COMPONENT_VARS    = re.compile(r"^/api/components/(\d+)/variants$")
_RE_COMPONENT_VAR_SEL = re.compile(r"^/api/component-variants/(\d+)/select$")
_RE_COMPONENT_VAR     = re.compile(r"^/api/component-variants/(\d+)$")
_RE_COMPONENT_LINK    = re.compile(r"^/api/components/(\d+)/link-screen$")

_RE_FLOWS        = re.compile(r"^/api/flows$")
_RE_FLOW         = re.compile(r"^/api/flows/(\d+)$")
_RE_FLOW_VARS    = re.compile(r"^/api/flows/(\d+)/variants$")
_RE_FLOW_VAR_SEL = re.compile(r"^/api/flow-variants/(\d+)/select$")
_RE_FLOW_VAR     = re.compile(r"^/api/flow-variants/(\d+)$")
_RE_FLOW_LINK    = re.compile(r"^/api/flows/(\d+)/link-screen$")


class FolioHandler(BaseHTTPRequestHandler):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _send_response_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        assert isinstance(body, bytes), "body must be bytes"
        assert content_type, "content_type must not be empty"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self._send_response_bytes(body, "application/json", status)

    def _send_html(self, html: str) -> None:
        assert html, "html must not be empty"
        body = html.encode("utf-8")
        self._send_response_bytes(body, "text/html; charset=utf-8", 200)

    def _serve_static(self, path: Path) -> None:
        assert path is not None, "path must not be None"
        if not path.exists():
            self._not_found()
            return
        mime, _ = mimetypes.guess_type(str(path))
        if mime is None:
            mime = "application/octet-stream"
        body = path.read_bytes()
        self._send_response_bytes(body, mime, 200)

    def _not_found(self, msg: str = "Not found") -> None:
        self._send_json({"error": msg}, 404)

    def _parse_multipart_file(self) -> bytes | None:
        """Extract first file payload from multipart/form-data body."""
        from email.parser import BytesParser
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        raw = f"Content-Type: {content_type}\r\n\r\n".encode() + body
        msg = BytesParser().parsebytes(raw)
        for part in msg.walk():
            cd = part.get("Content-Disposition", "")
            if "filename" in cd:
                return part.get_payload(decode=True)
        return None

    def log_message(self, *args) -> None:
        # Suppress default Apache-style per-request logging.
        pass

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_html(DASHBOARD_HTML)
            return

        match = _RE_DESIGN.match(path)
        if match:
            self._serve_static(db.DESIGN_DIR / unquote(match.group(1)))
            return

        match = _RE_SCREENSHOTS.match(path)
        if match:
            self._serve_static(db.SCREENSHOTS_DIR / unquote(match.group(1)))
            return

        if path == "/system.md":
            if not db.SYSTEM_MD_PATH.exists():
                self._not_found("system.md not found")
                return
            body = db.SYSTEM_MD_PATH.read_text(encoding="utf-8").encode("utf-8")
            self._send_response_bytes(body, "text/plain; charset=utf-8", 200)
            return

        if _RE_SCREENS.match(path):
            self._send_json(db.list_screens())
            return

        if _RE_COMPONENTS.match(path):
            self._send_json(db.list_components())
            return

        if _RE_FLOWS.match(path):
            self._send_json(db.list_flows())
            return

        self._not_found()

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if _RE_SCREENS.match(path):
            self._handle_create_screen()
            return

        match = _RE_SCREEN_VARS.match(path)
        if match:
            self._handle_create_screen_variant(int(match.group(1)))
            return

        if _RE_COMPONENTS.match(path):
            self._handle_create_component()
            return

        match = _RE_COMPONENT_VARS.match(path)
        if match:
            self._handle_create_component_variant(int(match.group(1)))
            return

        match = _RE_COMPONENT_LINK.match(path)
        if match:
            self._handle_link_component_screen(int(match.group(1)))
            return

        if _RE_FLOWS.match(path):
            self._handle_create_flow()
            return

        match = _RE_FLOW_VARS.match(path)
        if match:
            self._handle_create_flow_variant(int(match.group(1)))
            return

        match = _RE_FLOW_LINK.match(path)
        if match:
            self._handle_link_flow_screen(int(match.group(1)))
            return

        match = _RE_SCREENSHOT.match(path)
        if match:
            self._handle_upload_screenshot(int(match.group(1)))
            return

        self._not_found()

    def _handle_create_screen(self) -> None:
        data = self._read_json()
        try:
            screen = db.create_screen(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        first_file = data.get("file")
        if first_file:
            try:
                variant = db.create_screen_variant(
                    screen_id=screen["id"],
                    file=first_file,
                    label="v1",
                    ui_description=None,
                    notes=None,
                )
                db.select_screen_variant(variant["id"])
                screen = db.get_screen(screen["id"])
            except (ValueError, AssertionError) as exc:
                self._send_json({"error": str(exc)}, 400)
                return

        self._send_json(screen, 201)

    def _handle_create_component(self) -> None:
        data = self._read_json()
        try:
            component = db.create_component(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        first_file = data.get("file")
        if first_file:
            try:
                variant = db.create_component_variant(
                    component_id=component["id"],
                    file=first_file,
                    label="v1",
                    ui_description=None,
                    notes=None,
                )
                db.select_component_variant(variant["id"])
                component = db.get_component(component["id"])
            except (ValueError, AssertionError) as exc:
                self._send_json({"error": str(exc)}, 400)
                return

        self._send_json(component, 201)

    def _handle_create_flow(self) -> None:
        data = self._read_json()
        try:
            flow = db.create_flow(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(flow, 201)

    def _handle_create_screen_variant(self, screen_id: int) -> None:
        assert screen_id > 0, "screen_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_screen_variant(
                screen_id=screen_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_create_component_variant(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_component_variant(
                component_id=component_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_create_flow_variant(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_flow_variant(
                flow_id=flow_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_link_component_screen(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.link_component_screen(component_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_link_flow_screen(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.link_flow_screen(flow_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_upload_screenshot(self, variant_id: int) -> None:
        assert variant_id > 0, "variant_id must be positive"
        file_bytes = self._parse_multipart_file()
        if file_bytes is None:
            self._send_json({"error": "No file in request"}, 400)
            return

        db.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        safe_name = f"variant_{variant_id}.png"
        save_path = db.SCREENSHOTS_DIR / safe_name
        save_path.write_bytes(file_bytes)

        updated = db.update_variant_screenshot(variant_id, safe_name)
        if not updated:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return

        self._send_json({"screenshot": safe_name})

    # ------------------------------------------------------------------
    # PUT
    # ------------------------------------------------------------------

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        match = _RE_SCREEN_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_screen_variant)
            return

        match = _RE_SCREEN_PARENT.match(path)
        if match:
            self._handle_set_screen_parent(int(match.group(1)))
            return

        match = _RE_SCREEN.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_screen)
            return

        match = _RE_COMPONENT_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_component_variant)
            return

        match = _RE_COMPONENT.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_component)
            return

        match = _RE_FLOW_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_flow_variant)
            return

        match = _RE_FLOW.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_flow)
            return

        self._not_found()

    def _handle_update_entity(self, entity_id: int, update_fn) -> None:
        assert entity_id > 0, "entity_id must be positive"
        data = self._read_json()
        if not data:
            self._send_json({"error": "No fields provided"}, 400)
            return
        try:
            result = update_fn(entity_id, **data)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Entity {entity_id} not found"}, 404)
            return
        self._send_json(result)

    def _handle_select_variant(self, variant_id: int, select_fn) -> None:
        assert variant_id > 0, "variant_id must be positive"
        try:
            result = select_fn(variant_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return
        self._send_json(result)

    def _handle_set_screen_parent(self, screen_id: int) -> None:
        assert screen_id > 0, "screen_id must be positive"
        data = self._read_json()
        parent_id = data.get("parent_id")
        if parent_id is not None and (not isinstance(parent_id, int) or parent_id <= 0):
            self._send_json({"error": "parent_id must be a positive integer or null"}, 400)
            return
        try:
            result = db.set_screen_parent(screen_id, parent_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Screen {screen_id} not found"}, 404)
            return
        self._send_json(result)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        match = _RE_SCREEN_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_screen_variant)
            return

        match = _RE_SCREEN.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_screen)
            return

        match = _RE_COMPONENT_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_component_variant)
            return

        match = _RE_COMPONENT_LINK.match(path)
        if match:
            self._handle_unlink_component_screen(int(match.group(1)))
            return

        match = _RE_COMPONENT.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_component)
            return

        match = _RE_FLOW_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_flow_variant)
            return

        match = _RE_FLOW_LINK.match(path)
        if match:
            self._handle_unlink_flow_screen(int(match.group(1)))
            return

        match = _RE_FLOW.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_flow)
            return

        self._not_found()

    def _handle_delete_entity(self, entity_id: int, delete_fn) -> None:
        assert entity_id > 0, "entity_id must be positive"
        try:
            deleted = delete_fn(entity_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if not deleted:
            self._send_json({"error": f"Entity {entity_id} not found"}, 404)
            return
        self._send_json({"deleted": True})

    def _handle_delete_variant(self, variant_id: int, delete_fn) -> None:
        assert variant_id > 0, "variant_id must be positive"
        try:
            deleted = delete_fn(variant_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if not deleted:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return
        self._send_json({"deleted": True})

    def _handle_unlink_component_screen(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.unlink_component_screen(component_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_unlink_flow_screen(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.unlink_flow_screen(flow_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("FOLIO_PORT", 7842))

    _write_pid()
    atexit.register(_remove_pid)
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print(f"Folio → http://{host}:{port}  (PID {os.getpid()})")
    print(f"  DB:     {db.DB_PATH}")
    print(f"  Design: {db.DESIGN_DIR}")
    print(f"  System: {db.SYSTEM_MD_PATH}")
    HTTPServer((host, port), FolioHandler).serve_forever()
