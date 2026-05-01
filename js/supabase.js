// ============================================================
// PrecioVista — Cliente Supabase y funciones de base de datos
// Copyright © 2026 PrecioVista. CC BY-NC-SA 4.0
// ============================================================

// ── Configuración ──────────────────────────────────────────
// Reemplazá estos valores con los de tu proyecto en supabase.com
const SUPABASE_URL    = 'https://qcugckvhdclzuvveokmk.supabase.co';
const SUPABASE_ANON   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjdWdja3ZoZGNsenV2dmVva21rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1OTg5MzQsImV4cCI6MjA5MzE3NDkzNH0.mlC9Ei_rwOE-tdktirKlhRG9h3hWlThdLS2TYRYHqEw';
const ADMIN_EMAIL     = 'fepaviolo@gmail.com'; // Cambiá por tu email real

// ── Inicialización ──────────────────────────────────────────
let supabaseClient = null;

function initSupabase() {
  if (typeof window.supabase === 'undefined') {
    console.warn('PrecioVista: Supabase no cargado. Usando modo demo.');
    return null;
  }
  try {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON);
    return supabaseClient;
  } catch (e) {
    console.warn('PrecioVista: Error inicializando Supabase:', e.message);
    return null;
  }
}

function getClient() {
  if (!supabaseClient) supabaseClient = initSupabase();
  return supabaseClient;
}

function esModoDemo() {
  return !getClient() || SUPABASE_URL.includes('TU_PROYECTO');
}

// ── AUTENTICACIÓN ───────────────────────────────────────────

async function registrarUsuario(email, password, nombre) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo: configurá Supabase para registrarte.' } };
  const db = getClient();
  try {
    const { data, error } = await db.auth.signUp({
      email, password,
      options: { data: { nombre, rol: 'user', baneado: false } }
    });
    if (error) return { data: null, error };
    // Crear fila en tabla usuarios
    // CORRECCIÓN 1: data.user puede no existir si Supabase requiere confirmación de email.
    // En ese caso data.user es null hasta que el usuario confirme. Lo manejamos con un trigger
    // en Supabase (ver SUPABASE_SETUP.md) o insertamos solo si el user ya está disponible.
    if (data.user) {
      const { error: insertError } = await db.from('usuarios').insert({
        id:             data.user.id,
        email,
        nombre,
        rol:            'user',
        baneado:        false,
        reportes_count: 0
      });
      // No hacemos throw si falla el insert — el usuario ya quedó en auth.users
      // El insert puede fallar si el trigger de Supabase ya lo creó
      if (insertError && !insertError.message.includes('duplicate')) {
        console.warn('Insert usuarios:', insertError.message);
      }
    }
    return { data, error: null };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function loginEmail(email, password) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo: configurá Supabase.' } };
  const db = getClient();
  try {
    const { data, error } = await db.auth.signInWithPassword({ email, password });
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function loginGoogle() {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo: configurá Supabase.' } };
  const db = getClient();
  const { data, error } = await db.auth.signInWithOAuth({ provider: 'google' });
  return { data, error };
}

async function loginMicrosoft() {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo: configurá Supabase.' } };
  const db = getClient();
  const { data, error } = await db.auth.signInWithOAuth({ provider: 'azure' });
  return { data, error };
}

async function logout() {
  if (esModoDemo()) return;
  const db = getClient();
  await db.auth.signOut();
}

async function getUsuarioActual() {
  if (esModoDemo()) return null;
  const db = getClient();
  try {
    const { data: { user }, error } = await db.auth.getUser();
    // CORRECCIÓN 2: getUser() puede devolver error cuando no hay sesión activa.
    // El código original hacía destructuring sin verificar error, lo que causaba
    // un crash silencioso si la sesión era inválida o había expirado.
    if (error || !user) return null;
    const { data: perfil } = await db.from('usuarios').select('*').eq('id', user.id).single();
    return { ...user, perfil: perfil || null };
  } catch (e) {
    return null;
  }
}

function onAuthChange(callback) {
  // CORRECCIÓN 3: en modo demo onAuthChange no hacía nada, lo que dejaba
  // reportar.html esperando un callback que nunca llegaba.
  // Ahora disparamos el callback inmediatamente con null para que la UI
  // muestre el estado "no logueado" correctamente en modo demo.
  if (esModoDemo()) {
    callback(null);
    return;
  }
  const db = getClient();
  db.auth.onAuthStateChange((_event, session) => {
    callback(session?.user || null);
  });
}

function esAdmin(user) {
  if (!user) return false;
  return user.email === ADMIN_EMAIL || user.perfil?.rol === 'admin';
}

// ── PRECIOS ─────────────────────────────────────────────────

async function obtenerPrecios(productoId, paisId, provinciaId) {
  if (esModoDemo()) {
    return { data: generarPreciosDemo(paisId, productoId), error: null, demo: true };
  }
  const db = getClient();
  try {
    // CORRECCIÓN 4: filtrar por pais_id y provincia con .eq() sobre una columna
    // de tabla relacionada no funciona así en Supabase JS v2.
    // La forma correcta es hacer el join explícito o filtrar los comercios por separado.
    // Solución: traer los comercios del país primero, luego filtrar precios por esos IDs.
    let comerciosQuery = db.from('comercios').select('id').eq('pais_id', paisId);
    if (provinciaId) comerciosQuery = comerciosQuery.eq('provincia', provinciaId);
    const { data: comercios } = await comerciosQuery;
    const comercioIds = (comercios || []).map(c => c.id);

    if (comercioIds.length === 0) {
      return { data: generarPreciosDemo(paisId, productoId), error: null, demo: true };
    }

    const { data, error } = await db.from('precios')
      .select(`
        *,
        comercios(id, nombre, tipo, lat, lng, horario, logo_url, color, iniciales, direccion),
        productos(id, nombre, emoji)
      `)
      .eq('producto_id', productoId)
      .eq('verificado', true)
      .in('comercio_id', comercioIds)
      .order('precio', { ascending: true })
      .limit(20);

    return { data: data || [], error };
  } catch (e) {
    return { data: generarPreciosDemo(paisId, productoId), error: null, demo: true };
  }
}

async function reportarPrecio({ productoId, comercioId, precio, usuarioId }) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo: configurá Supabase.' } };
  const db = getClient();
  try {
    const { data, error } = await db.from('precios').insert({
      producto_id:  productoId,
      comercio_id:  comercioId,
      usuario_id:   usuarioId,
      precio,
      verificado:   false,
      created_at:   new Date().toISOString()
    });
    if (!error) {
      await db.rpc('incrementar_reportes', { uid: usuarioId });
    }
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function obtenerHistorial(productoId, comercioId) {
  if (esModoDemo()) {
    const base = 850 + Math.random() * 400;
    return { data: generarHistorial(base, '$'), error: null, demo: true };
  }
  const db = getClient();
  try {
    const desde = new Date();
    desde.setDate(desde.getDate() - 30);
    const { data, error } = await db.from('precios')
      .select('precio, created_at')
      .eq('producto_id', productoId)
      .eq('comercio_id', comercioId)
      .gte('created_at', desde.toISOString())
      .order('created_at', { ascending: true });
    return { data: data || [], error };
  } catch (e) {
    return { data: [], error: null };
  }
}

// ── BÚSQUEDA DE PRODUCTOS ───────────────────────────────────

async function buscarProductos(query) {
  if (esModoDemo() || !query || query.length < 2) {
    const q = (query || '').toLowerCase();
    return {
      data: PRODUCTOS_DEMO.filter(p => p.nombre.toLowerCase().includes(q)),
      error: null, demo: true
    };
  }
  const db = getClient();
  try {
    const { data, error } = await db.from('productos')
      .select('*')
      .ilike('nombre', `%${query}%`)
      .limit(12);
    return { data: data || [], error };
  } catch (e) {
    const q = query.toLowerCase();
    return { data: PRODUCTOS_DEMO.filter(p => p.nombre.toLowerCase().includes(q)), error: null, demo: true };
  }
}

// ── COMERCIOS ───────────────────────────────────────────────

async function obtenerComercio(comercioId) {
  if (esModoDemo()) {
    const cadena = Object.values(CADENAS).flat().find(c => c.id === comercioId);
    if (!cadena) return { data: null, error: { message: 'No encontrado' } };
    return {
      data: {
        ...cadena, id: comercioId,
        estrellas_promedio: 3.8 + Math.random(),
        resenas_count: Math.floor(Math.random() * 120) + 10,
        horario: '8:00 – 22:00',
        direccion: 'Dirección de ejemplo 123',
        lat: -34.6 + (Math.random() - 0.5) * 0.1,
        lng: -58.4 + (Math.random() - 0.5) * 0.1
      },
      error: null, demo: true
    };
  }
  const db = getClient();
  try {
    const { data, error } = await db.from('comercios').select('*').eq('id', comercioId).single();
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function calificarComercio(comercioId, usuarioId, estrellas) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo.' } };
  const db = getClient();
  try {
    const { data, error } = await db.from('resenas').upsert({
      comercio_id: comercioId, usuario_id: usuarioId,
      estrellas, created_at: new Date().toISOString()
    }, { onConflict: 'comercio_id,usuario_id' });
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

// ── ADMIN ───────────────────────────────────────────────────

async function adminGetUsuarios() {
  if (esModoDemo()) {
    return {
      data: [
        { id: '1', email: 'usuario1@mail.com', nombre: 'Juan Pérez',   rol: 'user', baneado: false, reportes_count: 14, created_at: '2026-01-10' },
        { id: '2', email: 'usuario2@mail.com', nombre: 'María García', rol: 'user', baneado: false, reportes_count: 32, created_at: '2026-02-05' },
        { id: '3', email: 'usuario3@mail.com', nombre: 'Carlos López', rol: 'user', baneado: true,  reportes_count: 3,  created_at: '2026-03-01' }
      ],
      error: null, demo: true
    };
  }
  const db = getClient();
  try {
    const { data, error } = await db.from('usuarios').select('*').order('created_at', { ascending: false });
    return { data: data || [], error };
  } catch (e) {
    return { data: [], error: { message: e.message } };
  }
}

async function adminBanearUsuario(usuarioId, motivo) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo.' } };
  const db = getClient();
  try {
    const { data, error } = await db.from('usuarios')
      .update({ baneado: true, motivo_ban: motivo })
      .eq('id', usuarioId);
    try {
      await db.functions.invoke('enviar-email-ban', { body: { usuarioId, motivo } });
    } catch (_) { /* email es opcional */ }
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function adminDesbanearUsuario(usuarioId) {
  if (esModoDemo()) return { data: null, error: { message: 'Modo demo.' } };
  const db = getClient();
  try {
    const { data, error } = await db.from('usuarios')
      .update({ baneado: false, motivo_ban: null })
      .eq('id', usuarioId);
    return { data, error };
  } catch (e) {
    return { data: null, error: { message: e.message } };
  }
}

async function adminGetReportes() {
  if (esModoDemo()) {
    return {
      data: [
        { id: '1', producto: 'Leche 1L',    comercio: 'Carrefour', precio: 850,  usuario: 'Juan Pérez',   created_at: '2026-04-25', verificado: false },
        { id: '2', producto: 'Arroz 1kg',   comercio: 'Coto',      precio: 620,  usuario: 'María García', created_at: '2026-04-26', verificado: true  },
        { id: '3', producto: 'Aceite 900ml',comercio: 'Disco',     precio: 1850, usuario: 'Carlos López', created_at: '2026-04-26', verificado: false }
      ],
      error: null, demo: true
    };
  }
  const db = getClient();
  try {
    const { data, error } = await db.from('precios')
      .select(`*, usuarios(nombre, email), productos(nombre), comercios(nombre)`)
      .order('created_at', { ascending: false })
      .limit(100);
    return { data: data || [], error };
  } catch (e) {
    return { data: [], error: { message: e.message } };
  }
}

// ── ESTADÍSTICAS GLOBALES ───────────────────────────────────

async function obtenerEstadisticas() {
  if (esModoDemo()) {
    return { precios: 1284, comercios: 87, usuarios: 342, error: null, demo: true };
  }
  const db = getClient();
  try {
    const [p, c, u] = await Promise.all([
      db.from('precios').select('*',   { count: 'exact', head: true }),
      db.from('comercios').select('*', { count: 'exact', head: true }),
      db.from('usuarios').select('*',  { count: 'exact', head: true }).eq('baneado', false)
    ]);
    return { precios: p.count || 0, comercios: c.count || 0, usuarios: u.count || 0, error: null };
  } catch (e) {
    return { precios: 0, comercios: 0, usuarios: 0, error: { message: e.message } };
  }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', initSupabase);

// ✓ supabase.js — completo
