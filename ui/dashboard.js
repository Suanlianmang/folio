// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
  section: 'flows',  // 'screens' | 'components' | 'flows'
  items: [],
  treeFlowId: null,
};

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

window.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.getElementById('project-name');
  const meta = document.querySelector('meta[name="folio-project"]');
  const projectName = (meta && meta.content) || document.title || 'Folio';
  titleEl.textContent = projectName;
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

  const hypothesisHtml = item.hypothesis
    ? `<div class="card-hypothesis">&#128161; ${escHtml(item.hypothesis)}</div>`
    : '';

  const focusHtml = item.focus
    ? `<div class="card-focus">Focus: ${escHtml(item.focus)}</div>`
    : '';

  const entityRationaleHtml = item.rationale
    ? `<div class="card-rationale" onclick="editEntityRationale(${item.id})">${escHtml(item.rationale)}</div>`
    : `<div class="card-rationale is-empty" onclick="editEntityRationale(${item.id})">+ rationale</div>`;

  const reviewBadge = item.needs_review
    ? `<span class="needs-review-badge">needs review</span>`
    : '';

  const screenComponents = item.components || [];
  const screenComponentsHtml = screenComponents.length > 0
    ? `<div class="linked-section">
         <div class="linked-heading">Components</div>
         <div class="linked-tags">${screenComponents.map(c => `<span class="linked-tag">${escHtml(c.name)}</span>`).join('')}</div>
       </div>`
    : '';

  const variantsHtml = renderVariants(item, 'screen');

  const selectedFile = item.selected_file || null;
  const previewBtn = selectedFile
    ? `<button class="btn btn-ghost" onclick="previewFile('${escAttr(selectedFile)}')">Preview selected</button>`
    : '';

  const reviewBtn = item.needs_review
    ? `<button class="btn btn-ghost" onclick="clearReview(${item.id})">Clear review</button>`
    : `<button class="btn btn-ghost" onclick="markReview(${item.id})">Mark for review</button>`;

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
      ${reviewBadge}
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    ${hypothesisHtml}
    ${focusHtml}
    ${entityRationaleHtml}
    ${parentHtml}
    ${screenComponentsHtml}
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      ${reviewBtn}
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

  const hypothesisHtml = item.hypothesis
    ? `<div class="card-hypothesis">&#128161; ${escHtml(item.hypothesis)}</div>`
    : '';

  const focusHtml = item.focus
    ? `<div class="card-focus">Focus: ${escHtml(item.focus)}</div>`
    : '';

  const entityRationaleHtml = item.rationale
    ? `<div class="card-rationale" onclick="editEntityRationale(${item.id})">${escHtml(item.rationale)}</div>`
    : `<div class="card-rationale is-empty" onclick="editEntityRationale(${item.id})">+ rationale</div>`;

  const reviewBadge = item.needs_review
    ? `<span class="needs-review-badge">needs review</span>`
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

  const reviewBtn = item.needs_review
    ? `<button class="btn btn-ghost" onclick="clearReview(${item.id})">Clear review</button>`
    : `<button class="btn btn-ghost" onclick="markReview(${item.id})">Mark for review</button>`;

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
      ${reviewBadge}
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    ${hypothesisHtml}
    ${focusHtml}
    ${entityRationaleHtml}
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
      ${reviewBtn}
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

  const hypothesisHtml = item.hypothesis
    ? `<div class="card-hypothesis">&#128161; ${escHtml(item.hypothesis)}</div>`
    : '';

  const focusHtml = item.focus
    ? `<div class="card-focus">Focus: ${escHtml(item.focus)}</div>`
    : '';

  const entityRationaleHtml = item.rationale
    ? `<div class="card-rationale" onclick="editEntityRationale(${item.id})">${escHtml(item.rationale)}</div>`
    : `<div class="card-rationale is-empty" onclick="editEntityRationale(${item.id})">+ rationale</div>`;

  const reviewBadge = item.needs_review
    ? `<span class="needs-review-badge">needs review</span>`
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

  const reviewBtn = item.needs_review
    ? `<button class="btn btn-ghost" onclick="clearReview(${item.id})">Clear review</button>`
    : `<button class="btn btn-ghost" onclick="markReview(${item.id})">Mark for review</button>`;

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
      ${reviewBadge}
      <button class="btn-danger btn" onclick="deleteEntity(${item.id})" title="Delete">&#x2715;</button>
    </div>
    ${metaHtml}
    ${hypothesisHtml}
    ${focusHtml}
    ${entityRationaleHtml}
    ${screenTreeHtml}
    <div class="variants-section">
      ${variantsHtml}
    </div>
    <div class="card-footer">
      <button class="btn" onclick="openAddVariantModal(${item.id})">+ Variant</button>
      <button class="btn" onclick="openLinkScreenModal(${item.id})">+ Link screen</button>
      ${viewTreeBtn}
      ${reviewBtn}
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

    const flagBadge = v.flag === 'needs-revision'
      ? `<span class="variant-flag-badge" title="${escAttr(v.flag_reason || '')}">needs revision</span>`
      : '';

    const rationaleHtml = v.rationale
      ? `<div class="variant-rationale" onclick="editVariantRationale(${v.id}, '${entityType}')">${escHtml(v.rationale)}</div>`
      : `<div class="variant-rationale is-empty" onclick="editVariantRationale(${v.id}, '${entityType}')">+ rationale</div>`;

    const flagBtn = v.flag === 'needs-revision'
      ? `<button class="btn btn-ghost" onclick="unflagVariant(${v.id}, '${entityType}')">Unflag</button>`
      : `<button class="btn btn-ghost" onclick="flagVariant(${v.id}, '${entityType}')">Flag</button>`;

    return `
    <div class="variant-row" id="variant-row-${v.id}">
      <div class="variant-row-main">
        <span class="${dotClass}">${dotChar}</span>
        <span class="variant-file" title="${escAttr(v.file)}">${escHtml(v.file)}</span>
        <span class="variant-label">${label}</span>
        ${flagBadge}
        <div class="variant-actions">
          <button class="btn btn-ghost" onclick="previewFile('${escAttr(v.file)}')">Preview</button>
          ${selectBtn}
          ${flagBtn}
          <button class="btn-danger btn" onclick="deleteVariant(${v.id}, '${entityType}')" title="Delete variant">&#x2715;</button>
        </div>
      </div>
      ${rationaleHtml}
    </div>`;
  }).join('');

  const compareBtn = variants.length >= 2
    ? `<button class="btn btn-ghost variants-compare-btn" onclick="openCompareModal(this)" data-variants="${escAttr(JSON.stringify(variants))}" data-name="${escAttr(item.name)}">Compare ↗</button>`
    : '';
  return `<div class="variants-heading-row"><span class="variants-heading">Variants (${variants.length})</span>${compareBtn}</div>${rows}`;
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
// Rendering — flagged tab
// ---------------------------------------------------------------------------

async function showFlaggedTab() {
  document.querySelectorAll('.sidebar-tab').forEach(b => b.classList.remove('active'));
  document.getElementById('flagged-tab').classList.add('active');
  document.getElementById('main-title').textContent = 'Flagged';

  const container = document.getElementById('items-container');
  container.innerHTML = '<div style="color:var(--text-muted);padding:20px">Loading&#8230;</div>';

  // Fetch all three sections
  const [screensRes, componentsRes, flowsRes] = await Promise.all([
    fetch('/api/screens'),
    fetch('/api/components'),
    fetch('/api/flows'),
  ]);
  const [screens, components, flows] = await Promise.all([
    screensRes.json(), componentsRes.json(), flowsRes.json(),
  ]);

  // Collect flagged variants with their parent entity info
  const flagged = [];
  for (const s of screens) {
    for (const v of (s.variants || [])) {
      if (v.flag === 'needs-revision') flagged.push({ entityType: 'screen', entity: s, variant: v });
    }
  }
  for (const c of components) {
    for (const v of (c.variants || [])) {
      if (v.flag === 'needs-revision') flagged.push({ entityType: 'component', entity: c, variant: v });
    }
  }
  for (const f of flows) {
    for (const v of (f.variants || [])) {
      if (v.flag === 'needs-revision') flagged.push({ entityType: 'flow', entity: f, variant: v });
    }
  }

  if (flagged.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No flagged variants.</p>
        <p style="font-size:12px;color:var(--text-muted)">Flag a variant with "needs revision" to surface it here.</p>
      </div>`;
    return;
  }

  container.innerHTML = flagged.map(({ entityType, entity, variant }) => {
    const reasonHtml = variant.flag_reason
      ? `<div class="flagged-reason">${escHtml(variant.flag_reason)}</div>`
      : '';
    const previewBtn = `<button class="btn btn-ghost" onclick="previewFile('${escAttr(variant.file)}')">Preview</button>`;
    const unflagBtn  = `<button class="btn btn-ghost" onclick="unflagVariantAndReload(${variant.id}, '${entityType}')">Unflag</button>`;
    return `
    <div class="card flagged-card">
      <div class="card-header">
        <span class="card-name">${escHtml(entity.name)}</span>
        <span class="type-badge">${entityType}</span>
        <span class="variant-flag-badge">needs revision</span>
      </div>
      <div style="padding:10px 16px">
        <div style="font-size:12px;font-family:'SF Mono','Menlo',monospace;color:var(--text-secondary);margin-bottom:4px">${escHtml(variant.file)}${variant.label ? ' [' + escHtml(variant.label) + ']' : ''}</div>
        ${reasonHtml}
      </div>
      <div class="card-footer">
        ${previewBtn}
        ${unflagBtn}
      </div>
    </div>`;
  }).join('');
}

async function unflagVariantAndReload(variantId, entityType) {
  const res = await fetch(`/api/${_variantApiPrefix(entityType)}/${variantId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ flag: null, flag_reason: null }),
  });
  if (!res.ok) { alert('Failed to unflag'); return; }
  showFlaggedTab();
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
  const prefix = _variantApiPrefix(entityType);
  const res = await fetch(`/api/${prefix}/${variantId}/select`, { method: 'PUT' });
  if (!res.ok) { alert('Failed to select variant'); return; }

  const rationale = prompt('Why did this variant win? (optional — press Enter to skip)', '');
  if (rationale !== null && rationale.trim()) {
    await fetch(`/api/${prefix}/${variantId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rationale: rationale.trim() }),
    });
  }
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
    </div>
    <div class="form-field">
      <label class="form-label">Rationale</label>
      <textarea class="form-textarea" id="f-vrationale" placeholder="What hypothesis is this testing?"></textarea>
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
  const rationale      = document.getElementById('f-vrationale').value.trim() || null;

  if (!file) { alert('File is required'); return; }

  const res = await fetch(`/api/${state.section}/${entityId}/variants`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ file, label, ui_description, notes, rationale }),
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
      arrows += `<path d="M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2 - 7}" fill="none" stroke="#3a4458" stroke-width="1.5"/>`;
      arrows += `<polygon points="${x2},${y2} ${x2 - 5},${y2 - 8} ${x2 + 5},${y2 - 8}" fill="#3a4458"/>`;
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

// ---------------------------------------------------------------------------
// Variant patch actions
// ---------------------------------------------------------------------------

function _variantApiPrefix(entityType) {
  return entityType === 'screen'    ? 'screen-variants'
       : entityType === 'component' ? 'component-variants'
       : 'flow-variants';
}

async function patchVariant(variantId, entityType, body) {
  const res = await fetch(`/api/${_variantApiPrefix(entityType)}/${variantId}`, {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    alert(data.error || 'Failed to update variant');
    return false;
  }
  loadSection();
  return true;
}

async function flagVariant(variantId, entityType) {
  const reason = prompt('Reason for flagging (optional):', '');
  if (reason === null) return;
  await patchVariant(variantId, entityType, { flag: 'needs-revision', flag_reason: reason.trim() || null });
}

async function unflagVariant(variantId, entityType) {
  await patchVariant(variantId, entityType, { flag: null, flag_reason: null });
}

async function editVariantRationale(variantId, entityType) {
  const allItems = state ? (state.items || []) : [];
  let current = '';
  for (const item of allItems) {
    const match = (item.variants || []).find(v => v.id === variantId);
    if (match) { current = match.rationale || ''; break; }
  }
  const next = prompt('Design rationale (why this variant):', current);
  if (next === null) return;
  await patchVariant(variantId, entityType, { rationale: next.trim() || null });
}

async function editEntityRationale(entityId) {
  const allItems = state ? (state.items || []) : [];
  const item = allItems.find(i => i.id === entityId);
  const current = item ? (item.rationale || '') : '';
  const next = prompt('Design rationale (why this direction):', current);
  if (next === null) return;
  const res = await fetch(`/api/${state.section}/${entityId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rationale: next.trim() || null }),
  });
  if (!res.ok) { alert('Failed to update rationale'); return; }
  loadSection();
}

function openCompareModal(btn) {
  const variants = JSON.parse(btn.dataset.variants);
  const itemName = btn.dataset.name;

  document.getElementById('modal-title').textContent = `Compare variants — ${itemName}`;

  const cols = variants.map(v => {
    const label = v.label ? ` [${escHtml(v.label)}]` : '';
    const rationaleHtml = v.rationale
      ? `<div class="compare-rationale">${escHtml(v.rationale)}</div>`
      : '';
    return `
      <div class="compare-col">
        <div class="compare-col-header">
          <span class="compare-col-file" title="${escAttr(v.file)}">${escHtml(v.file)}${label}</span>
          <button class="btn btn-ghost" onclick="window.open('/design/${encodeURIComponent(v.file)}','_blank')">↗</button>
        </div>
        ${rationaleHtml}
        <iframe class="compare-iframe" src="/design/${encodeURIComponent(v.file)}" loading="lazy"></iframe>
      </div>`;
  }).join('');

  document.getElementById('modal-body').innerHTML = `<div class="compare-grid">${cols}</div>`;
  document.getElementById('modal-footer').innerHTML = `<button class="btn" onclick="closeModalDirect()">Close</button>`;
  document.getElementById('modal-backdrop').classList.add('open');
}

async function markReview(entityId) {
  await fetch(`/api/${state.section}/${entityId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ needs_review: 1 }),
  });
  loadSection();
}

async function clearReview(entityId) {
  await fetch(`/api/${state.section}/${entityId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ needs_review: 0 }),
  });
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
