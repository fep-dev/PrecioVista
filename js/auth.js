// ============================================================
// PrecioVista — Autenticación: modales login/registro
// Copyright © 2026 PrecioVista. CC BY-NC-SA 4.0
// ============================================================

let usuarioActual = null;

// ── Detectar base path para rutas (GitHub Pages vs local) ───
function getBasePath() {
  const path = window.location.pathname;
  // En GitHub Pages el proyecto vive bajo /preciovista/
  // Detectamos si estamos en un subdirectorio
  const match = path.match(/^(\/[^/]+)\//);
  if (match && match[1] !== '' && !path.startsWith('/index.html') && !path.startsWith('/pages/')) {
    return match[1];
  }
  return '';
}

function resolverRuta(ruta) {
  // ruta siempre empieza con / (ej: /index.html, /pages/reportar.html)
  return getBasePath() + ruta;
}

// ── Estado de sesión ────────────────────────────────────────
async function inicializarAuth() {
  usuarioActual = await getUsuarioActual();
  actualizarUIAuth(usuarioActual);
  onAuthChange(async (user) => {
    if (user) {
      usuarioActual = await getUsuarioActual();
    } else {
      usuarioActual = null;
    }
    actualizarUIAuth(usuarioActual);
  });
}

function actualizarUIAuth(user) {
  const btnAuth    = document.getElementById('btn-auth');
  const btnLogout  = document.getElementById('btn-logout');
  const navUser    = document.getElementById('nav-user');

  if (user) {
    if (btnAuth)   { btnAuth.textContent = 'Reportar precio'; btnAuth.onclick = () => window.location.href = resolverRuta('/pages/reportar.html'); }
    if (btnLogout) btnLogout.style.display = 'block';
    if (navUser)   { navUser.textContent = user.perfil?.nombre || user.email; navUser.style.display = 'flex'; }
  } else {
    if (btnAuth)   { btnAuth.textContent = 'Ingresar'; btnAuth.onclick = abrirLogin; }
    if (btnLogout) btnLogout.style.display = 'none';
    if (navUser)   navUser.style.display = 'none';
  }
}

function getUsuarioLocal() { return usuarioActual; }
function estaLogueado()    { return !!usuarioActual; }

// ── Modal Login ─────────────────────────────────────────────
function abrirLogin() {
  const overlay = document.getElementById('modal-login');
  if (!overlay) { crearModalLogin(); return; }
  overlay.classList.add('open');
}

function cerrarLogin() {
  const overlay = document.getElementById('modal-login');
  if (overlay) overlay.classList.remove('open');
}

function crearModalLogin() {
  const html = `
  <div class="modal-overlay" id="modal-login">
    <div class="modal">
      <button class="modal-close" onclick="cerrarLogin()">✕</button>
      <div class="modal-logo">
        <img src="${resolverRuta('/assets/logo.png')}" alt="PrecioVista" style="width:56px;height:56px;object-fit:contain">
      </div>
      <h2 class="modal-title">Bienvenido</h2>
      <p class="modal-sub">Ingresá para reportar precios y ayudar a la comunidad</p>

      <div id="login-form">
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-input" id="login-email" placeholder="tu@email.com">
          <span class="form-error" id="login-email-error"></span>
        </div>
        <div class="form-group">
          <label class="form-label">Contraseña</label>
          <input type="password" class="form-input" id="login-password" placeholder="••••••••">
          <span class="form-error" id="login-pass-error"></span>
        </div>
        <div id="login-error" class="form-error" style="display:none;margin-bottom:10px;font-size:0.83rem"></div>
        <button class="btn btn-primary" id="btn-login-submit" onclick="submitLogin()">
          <span>Ingresar</span>
        </button>

        <div class="divider"><div class="divider-line"></div><span class="divider-text">o continuá con</span><div class="divider-line"></div></div>

        <button class="btn btn-google" style="margin-bottom:8px" onclick="submitGoogle()">
          <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="Google">
          Continuar con Google
        </button>
        <button class="btn btn-microsoft" onclick="submitMicrosoft()">
          <span style="font-weight:700">⊞</span> Continuar con Microsoft
        </button>

        <p style="text-align:center;font-size:0.82rem;margin-top:1.2rem;color:var(--text-2)">
          ¿No tenés cuenta? <a href="#" style="color:var(--wood);font-weight:600" onclick="abrirRegistro();return false">Registrate gratis</a>
        </p>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
  document.getElementById('modal-login').addEventListener('click', e => {
    if (e.target.id === 'modal-login') cerrarLogin();
  });
  document.getElementById('modal-login').classList.add('open');
  // Enter en password
  document.getElementById('login-password')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') submitLogin();
  });
}

async function submitLogin() {
  const email    = document.getElementById('login-email')?.value.trim();
  const password = document.getElementById('login-password')?.value;
  const errEl    = document.getElementById('login-error');
  const btn      = document.getElementById('btn-login-submit');

  limpiarErrores('login');
  if (!email)    { mostrarError('login-email-error', 'Ingresá tu email'); return; }
  if (!password) { mostrarError('login-pass-error', 'Ingresá tu contraseña'); return; }

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Ingresando...';

  const { data, error } = await loginEmail(email, password);
  btn.disabled = false;
  btn.innerHTML = '<span>Ingresar</span>';

  if (error) {
    if (errEl) { errEl.textContent = traducirError(error.message); errEl.style.display = 'block'; }
    return;
  }

  cerrarLogin();
  mostrarToast('¡Bienvenido de nuevo! 👋', 'success');
}

async function submitGoogle() {
  const { error } = await loginGoogle();
  if (error) mostrarToast('Error al conectar con Google', 'error');
}

async function submitMicrosoft() {
  const { error } = await loginMicrosoft();
  if (error) mostrarToast('Error al conectar con Microsoft', 'error');
}

// ── Modal Registro ──────────────────────────────────────────
function abrirRegistro() {
  cerrarLogin();
  const overlay = document.getElementById('modal-registro');
  if (!overlay) { crearModalRegistro(); return; }
  overlay.classList.add('open');
}

function cerrarRegistro() {
  const overlay = document.getElementById('modal-registro');
  if (overlay) overlay.classList.remove('open');
}

function crearModalRegistro() {
  const html = `
  <div class="modal-overlay" id="modal-registro">
    <div class="modal">
      <button class="modal-close" onclick="cerrarRegistro()">✕</button>
      <div class="modal-logo">✍️</div>
      <h2 class="modal-title">Crear cuenta</h2>
      <p class="modal-sub">Unite a la comunidad y ayudá a otros a comprar mejor</p>

      <div id="registro-form">
        <div class="form-group">
          <label class="form-label">Nombre completo</label>
          <input type="text" class="form-input" id="reg-nombre" placeholder="Tu nombre real">
          <span class="form-error" id="reg-nombre-error"></span>
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input type="email" class="form-input" id="reg-email" placeholder="tu@email.com">
          <span class="form-error" id="reg-email-error"></span>
        </div>
        <div class="form-group">
          <label class="form-label">Contraseña</label>
          <input type="password" class="form-input" id="reg-password" placeholder="Mínimo 8 caracteres">
          <span class="form-hint">Mínimo 8 caracteres</span>
          <span class="form-error" id="reg-pass-error"></span>
        </div>

        <div class="commit-box">
          <strong>Compromiso de datos verídicos</strong><br>
          Al registrarte te comprometés a cargar únicamente precios reales que hayas visto personalmente.
          Cargar precios falsos o incorrectos puede resultar en el bloqueo permanente de tu cuenta.
        </div>

        <label class="commit-check" style="margin-bottom:1.2rem">
          <input type="checkbox" id="reg-acepta">
          Entendí y acepto el compromiso de datos verídicos
        </label>

        <div id="reg-error" class="form-error" style="display:none;margin-bottom:10px;font-size:0.83rem"></div>
        <button class="btn btn-wood" id="btn-reg-submit" onclick="submitRegistro()">
          <span>Crear cuenta gratis</span>
        </button>

        <div class="divider"><div class="divider-line"></div><span class="divider-text">o registrate con</span><div class="divider-line"></div></div>

        <button class="btn btn-google" style="margin-bottom:8px" onclick="submitGoogle()">
          <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="Google">
          Registrarse con Google
        </button>
        <button class="btn btn-microsoft" onclick="submitMicrosoft()">
          <span style="font-weight:700">⊞</span> Registrarse con Microsoft
        </button>

        <p style="text-align:center;font-size:0.82rem;margin-top:1.2rem;color:var(--text-2)">
          ¿Ya tenés cuenta? <a href="#" style="color:var(--wood);font-weight:600" onclick="abrirLogin();return false">Ingresá</a>
        </p>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
  document.getElementById('modal-registro').addEventListener('click', e => {
    if (e.target.id === 'modal-registro') cerrarRegistro();
  });
  document.getElementById('modal-registro').classList.add('open');
}

async function submitRegistro() {
  const nombre   = document.getElementById('reg-nombre')?.value.trim();
  const email    = document.getElementById('reg-email')?.value.trim();
  const password = document.getElementById('reg-password')?.value;
  const acepta   = document.getElementById('reg-acepta')?.checked;
  const errEl    = document.getElementById('reg-error');
  const btn      = document.getElementById('btn-reg-submit');

  limpiarErrores('reg');
  let valido = true;
  if (!nombre)         { mostrarError('reg-nombre-error', 'Ingresá tu nombre'); valido = false; }
  if (!email)          { mostrarError('reg-email-error', 'Ingresá tu email'); valido = false; }
  if (!password || password.length < 8) { mostrarError('reg-pass-error', 'La contraseña debe tener al menos 8 caracteres'); valido = false; }
  if (!acepta)         { if(errEl){ errEl.textContent = 'Debés aceptar el compromiso de datos verídicos'; errEl.style.display = 'block'; } valido = false; }
  if (!valido) return;

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Creando cuenta...';

  const { data, error } = await registrarUsuario(email, password, nombre);
  btn.disabled = false;
  btn.innerHTML = '<span>Crear cuenta gratis</span>';

  if (error) {
    if (errEl) { errEl.textContent = traducirError(error.message); errEl.style.display = 'block'; }
    return;
  }

  cerrarRegistro();
  mostrarToast('¡Cuenta creada! Revisá tu email para confirmar. 📧', 'success');
}

// ── Modal Ubicación ─────────────────────────────────────────
function abrirUbicacion() {
  const overlay = document.getElementById('modal-ubicacion');
  if (!overlay) { crearModalUbicacion(); return; }
  overlay.classList.add('open');
}

function cerrarUbicacion() {
  const overlay = document.getElementById('modal-ubicacion');
  if (overlay) overlay.classList.remove('open');
}

function crearModalUbicacion() {
  const provActual  = localStorage.getItem('pv_provincia') || '';
  const ciudadActual = localStorage.getItem('pv_ciudad') || '';
  const ciudades    = provActual ? getCiudades(provActual) : [];

  const html = `
  <div class="modal-overlay" id="modal-ubicacion">
    <div class="modal" style="max-width:520px">
      <button class="modal-close" onclick="cerrarUbicacion()">✕</button>
      <div class="modal-logo">📍</div>
      <h2 class="modal-title">Tu ubicación</h2>
      <p class="modal-sub">Elegí tu provincia y ciudad para ver precios cercanos</p>

      <div class="form-group">
        <label class="form-label">Provincia</label>
        <select class="form-input form-select" id="sel-provincia" onchange="actualizarCiudades()">
          <option value="">Todas las provincias</option>
          ${getPais('ar').provincias.map(p =>
            `<option value="${p}" ${p === provActual ? 'selected' : ''}>${p}</option>`
          ).join('')}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Ciudad</label>
        <select class="form-input form-select" id="sel-ciudad">
          <option value="">Todas las ciudades</option>
          ${ciudades.map(c =>
            `<option value="${c}" ${c === ciudadActual ? 'selected' : ''}>${c}</option>`
          ).join('')}
        </select>
      </div>

      <button class="btn btn-wood" onclick="guardarUbicacion()">
        📍 Guardar ubicación
      </button>
      <button class="btn btn-secondary" style="margin-top:8px" onclick="detectarUbicacion()">
        🛰 Detectar automáticamente
      </button>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
  document.getElementById('modal-ubicacion').addEventListener('click', e => {
    if (e.target.id === 'modal-ubicacion') cerrarUbicacion();
  });
  document.getElementById('modal-ubicacion').classList.add('open');
}

function actualizarCiudades() {
  const provincia = document.getElementById('sel-provincia')?.value || '';
  const sel       = document.getElementById('sel-ciudad');
  if (!sel) return;
  const ciudades  = provincia ? getCiudades(provincia) : [];
  sel.innerHTML   = '<option value="">Todas las ciudades</option>' +
    ciudades.map(c => `<option value="${c}">${c}</option>`).join('');
}

function cargarProvincias() {
  // No necesario — solo Argentina, provincias cargadas directamente en crearModalUbicacion
}

function guardarUbicacion() {
  const provincia = document.getElementById('sel-provincia')?.value || '';
  const ciudad    = document.getElementById('sel-ciudad')?.value || '';
  localStorage.setItem('pv_pais', 'ar');
  localStorage.setItem('pv_provincia', provincia);
  localStorage.setItem('pv_ciudad', ciudad);
  actualizarNavUbicacion('ar', provincia, ciudad);
  cerrarUbicacion();
  mostrarToast('Ubicación guardada ✓', 'success');
  if (typeof recargarResultados === 'function') recargarResultados();
}

function detectarUbicacion() {
  if (!navigator.geolocation) {
    mostrarToast('Tu navegador no soporta geolocalización', 'error'); return;
  }
  mostrarToast('Detectando ubicación...', 'info');
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      let pais = 'ar';
      if (lat > 35 && lat < 44 && lng > -10 && lng < 5)    pais = 'es';
      else if (lat < -17 && lat > -56 && lng > -76 && lng < -65) pais = 'cl';
      else if (lat > 14 && lat < 33 && lng > -118 && lng < -86)  pais = 'mx';
      else if (lat < -10 && lat > -22 && lng > -81 && lng < -68) pais = 'pe';
      else if (lat < -30 && lat > -35 && lng > -59 && lng < -53) pais = 'uy';

      const selPais = document.getElementById('sel-provincia');
      if (selPais) mostrarToast('Ubicación detectada ✓', 'success');
    },
    () => mostrarToast('No se pudo obtener la ubicación', 'error')
  );
}

function actualizarNavUbicacion(paisId, provincia, ciudad) {
  const el   = document.getElementById('nav-location-text');
  const pais = getPais(paisId);
  if (!el || !pais) return;
  if (ciudad)       el.textContent = `${pais.bandera} ${ciudad}`;
  else if (provincia) el.textContent = `${pais.bandera} ${provincia}`;
  else              el.textContent = `${pais.bandera} ${pais.nombre}`;
}

// ── Helpers ─────────────────────────────────────────────────
function mostrarError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.add('show'); el.style.display = 'block'; }
}

function limpiarErrores(prefix) {
  document.querySelectorAll(`[id^="${prefix}-"][id$="-error"]`).forEach(el => {
    el.textContent = ''; el.classList.remove('show'); el.style.display = 'none';
  });
  const general = document.getElementById(`${prefix}-error`);
  if (general) { general.textContent = ''; general.style.display = 'none'; }
}

function traducirError(msg) {
  if (!msg) return 'Error desconocido';
  if (msg.includes('Invalid login'))           return 'Email o contraseña incorrectos';
  if (msg.includes('Email not confirmed'))     return 'Confirmá tu email antes de ingresar';
  if (msg.includes('User already registered')) return 'Este email ya está registrado';
  if (msg.includes('Password should be'))      return 'La contraseña debe tener al menos 8 caracteres';
  if (msg.includes('network'))                 return 'Error de conexión. Verificá tu internet';
  return msg;
}

async function cerrarSesion() {
  await logout();
  mostrarToast('Sesión cerrada', 'info');
  setTimeout(() => window.location.href = resolverRuta('/index.html'), 800);
}

// ── Inicializar ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  inicializarAuth();
  const paisId    = localStorage.getItem('pv_pais') || 'ar';
  const provincia = localStorage.getItem('pv_provincia') || '';
  const ciudad    = localStorage.getItem('pv_ciudad') || '';
  actualizarNavUbicacion(paisId, provincia, ciudad);
});

// ✓ auth.js — completo
