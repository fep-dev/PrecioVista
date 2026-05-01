// ============================================================
// PrecioVista — Lógica principal y utilidades compartidas
// Copyright © 2026 PrecioVista. CC BY-NC-SA 4.0
// ============================================================

// ── Toast notifications ─────────────────────────────────────
function mostrarToast(mensaje, tipo = 'info', duracion = 3500) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const iconos = { success: '✅', error: '❌', info: '💡' };
  const toast  = document.createElement('div');
  toast.className = `toast ${tipo}`;
  toast.innerHTML = `<span>${iconos[tipo] || '💡'}</span><span>${mensaje}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slide-in 0.3s ease reverse';
    setTimeout(() => toast.remove(), 280);
  }, duracion);
}

// ── Render helpers compartidos ──────────────────────────────

function renderLogoComercio(cadena, size = 36) {
  if (cadena.logo) {
    return `<div class="price-logo" style="width:${size}px;height:${size}px">
      <img src="${cadena.logo}" alt="${cadena.nombre}" onerror="this.parentElement.innerHTML='${cadena.iniciales}'">
    </div>`;
  }
  return `<div class="price-logo-fallback" style="width:${size}px;height:${size}px;background:${cadena.color || '#2563EB'}">
    ${cadena.iniciales}
  </div>`;
}

function renderStoreCard(cadena, onclick = '') {
  const badge = cadena.tipo === 'super' ? 'badge-super' : 'badge-kiosk';
  const label = cadena.tipo === 'super' ? 'Supermercado' : 'Kiosco';
  const logoHtml = cadena.logo
    ? `<div class="store-logo-wrap"><img src="${cadena.logo}" alt="${cadena.nombre}" onerror="this.parentElement.outerHTML='<div class=store-logo-fallback style=background:${cadena.color};color:white>${cadena.iniciales}</div>'"></div>`
    : `<div class="store-logo-fallback" style="background:${cadena.color};color:white">${cadena.iniciales}</div>`;
  return `
  <div class="store-card" ${onclick ? `onclick="${onclick}"` : ''}>
    ${logoHtml}
    <span class="store-name">${cadena.nombre}</span>
    <span class="store-type-badge ${badge}">${label}</span>
  </div>`;
}

function renderCountryCard(pais, activo = false, onclick = '') {
  return `
  <div class="country-card ${activo ? 'active' : ''}" ${onclick ? `onclick="${onclick}"` : ''} data-pais="${pais.id}">
    <span class="country-flag">${pais.bandera}</span>
    <div class="country-name">${pais.nombre}</div>
    <div class="country-count">${(CADENAS[pais.id] || []).length} cadenas</div>
  </div>`;
}

function renderEstrellas(promedio, total = 0, editable = false, comercioId = '') {
  const llenas = Math.round(promedio);
  let html = '<div class="stars">';
  for (let i = 1; i <= 5; i++) {
    const cls = i <= llenas ? 'star' : 'star empty';
    const onclick = editable ? `onclick="calificar(${i},'${comercioId}')"` : '';
    html += `<span class="${cls}" ${onclick}>★</span>`;
  }
  html += `</div>`;
  if (total > 0) html += `<span class="stars-count">${promedio.toFixed(1)} (${total} reseñas)</span>`;
  return html;
}

// ── Número animado ──────────────────────────────────────────
function animarNumero(el, objetivo, duracion = 1200) {
  if (!el) return;
  const inicio   = 0;
  const step     = (objetivo / duracion) * 16;
  let actual     = inicio;
  const interval = setInterval(() => {
    actual += step;
    if (actual >= objetivo) { actual = objetivo; clearInterval(interval); }
    el.textContent = Math.round(actual).toLocaleString('es-AR');
  }, 16);
}

// ── Página de inicio ────────────────────────────────────────
async function iniciarHome() {
  const paisId = localStorage.getItem('pv_pais') || 'ar';
  renderPaises(paisId);
  renderCadenas(paisId);
  await cargarEstadisticas();
  configurarBuscador();
}

function renderPaises(paisActivo) {
  const grid = document.getElementById('countries-grid');
  if (!grid) return;
  grid.innerHTML = PAISES.map(p =>
    renderCountryCard(p, p.id === paisActivo, `seleccionarPais('${p.id}')`)
  ).join('');
}

function seleccionarPais(paisId) {
  localStorage.setItem('pv_pais', paisId);
  localStorage.removeItem('pv_provincia');
  // Actualizar UI
  document.querySelectorAll('.country-card').forEach(el => {
    el.classList.toggle('active', el.dataset.pais === paisId);
  });
  renderCadenas(paisId);
  const pais = getPais(paisId);
  const title = document.getElementById('stores-title');
  if (title) title.textContent = `Cadenas en ${pais.nombre}`;
  actualizarNavUbicacion(paisId, '');
}

function renderCadenas(paisId) {
  const grid = document.getElementById('stores-grid');
  if (!grid) return;
  const cadenas = getCadenas(paisId);
  grid.innerHTML = cadenas.map(c =>
    renderStoreCard(c, `irABuscar('${c.id}','${paisId}')`)
  ).join('');
}

function irABuscar(comercioId, paisId) {
  window.location.href = `pages/buscar.html?comercio=${comercioId}&pais=${paisId}`;
}

async function cargarEstadisticas() {
  const { precios, comercios, usuarios } = await obtenerEstadisticas();
  setTimeout(() => {
    const elP = document.querySelector('#stat-precios span');
    const elC = document.querySelector('#stat-comercios span');
    const elU = document.querySelector('#stat-usuarios span');
    if (elP) animarNumero(elP, precios || 1284);
    if (elC) animarNumero(elC, comercios || 87);
    if (elU) animarNumero(elU, usuarios || 342);
  }, 400);
}

function configurarBuscador() {
  const input = document.getElementById('main-search');
  if (!input) return;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') buscar();
  });
}

function buscar() {
  const query = document.getElementById('main-search')?.value.trim();
  if (!query) { mostrarToast('Escribí un producto para buscar', 'info'); return; }
  window.location.href = `pages/buscar.html?q=${encodeURIComponent(query)}`;
}

function buscarProducto(termino) {
  window.location.href = `pages/buscar.html?q=${encodeURIComponent(termino)}`;
}

// ── Helpers de URL ──────────────────────────────────────────
function getParam(nombre) {
  return new URLSearchParams(window.location.search).get(nombre) || '';
}

// ── Inicializar según página ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  if (path.endsWith('index.html') || path === '/' || path.endsWith('/')) {
    iniciarHome();
  }
});

// ✓ app.js — completo
