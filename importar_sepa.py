#!/usr/bin/env python3
# ============================================================
# importar_sepa.py — Importador diario de precios SEPA
# PrecioVista © 2026 — CC BY-NC-SA 4.0
# ============================================================
# Estructura SEPA (documentación oficial Res. N° 678/2020):
# ZIP externo → N ZIPs internos (uno por comercio)
# Cada ZIP interno contiene hasta 3 archivos:
#   - comercio.csv    → id_comercio, id_bandera, comercio_cuit,
#                       comercio_razon_social, comercio_bandera_nombre...
#   - sucursales.csv  → id_sucursal, nombre, provincia, localidad, lat, lng...
#   - productos.csv   → id_comercio, id_sucursal, id_bandera, id_producto,
#                       productos_descripcion, presentacion, precio_lista,
#                       precio_referencia, precio_unitario_promo1, etc.
# ============================================================

import os, sys, csv, zipfile, requests, tempfile, datetime, io, re
from io import TextIOWrapper
from supabase import create_client

sys.path.insert(0, os.path.dirname(__file__))
from config_sepa import PRODUCTOS, CADENAS, PROVINCIAS_FILTRO, SEPA_URLS, MONEDA

# ── Conexión Supabase ───────────────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('ERROR: Faltan variables de entorno SUPABASE_URL y SUPABASE_SERVICE_KEY')
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)

def log(msg):
    print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}', flush=True)

# ── Helpers ─────────────────────────────────────────────────

def normalizar(texto):
    """Minúsculas, sin tildes, sin espacios extra."""
    if not texto:
        return ''
    t = str(texto).lower().strip()
    for c, s in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),
                 ('à','a'),('è','e'),('ì','i'),('ò','o'),('ù','u'),
                 ('ä','a'),('ë','e'),('ï','i'),('ö','o'),('ü','u'),('ñ','n')]:
        t = t.replace(c, s)
    return ' '.join(t.split())

def detectar_producto(descripcion):
    """Busca si la descripción matchea alguna keyword configurada."""
    n = normalizar(descripcion)
    if not n:
        return None
    for pid, keywords in PRODUCTOS.items():
        for kw in keywords:
            if normalizar(kw) in n:
                return pid
    return None

def detectar_cadena(nombre_bandera):
    """
    Busca si el nombre de bandera matchea alguna cadena.
    Usa word boundary para evitar falsos positivos.
    """
    n = normalizar(nombre_bandera)
    if not n:
        return None
    for cid, nombres in CADENAS.items():
        for nombre in nombres:
            patron = r'\b' + re.escape(normalizar(nombre)) + r'\b'
            if re.search(patron, n):
                return cid
    return None

def parsear_precio(raw):
    """
    Parsea precio manejando formato argentino.
    '1.250,50' → 1250.50
    '1250,50'  → 1250.50
    '1250.50'  → 1250.50
    """
    if not raw:
        return None
    try:
        t = str(raw).strip()
        if not t or t in ('0', '0.0', '0,0', '0,00', '0.00'):
            return None
        if ',' in t and '.' in t:
            # Formato argentino: punto=miles, coma=decimal
            t = t.replace('.', '').replace(',', '.')
        elif ',' in t:
            t = t.replace(',', '.')
        precio = float(t)
        return round(precio, 2) if precio > 0 else None
    except (ValueError, TypeError):
        return None

def provincia_permitida(nombre_prov):
    """Verifica si la provincia está en el filtro. Sin tildes."""
    if not PROVINCIAS_FILTRO:
        return True
    n = normalizar(nombre_prov)
    if not n:
        # Sin provincia — aceptar si no filtramos por provincia
        return True
    n = n.replace('ciudad autonoma de buenos aires', 'ciudad de buenos aires')
    for p in PROVINCIAS_FILTRO:
        pn = normalizar(p).replace('ciudad autonoma de buenos aires', 'ciudad de buenos aires')
        if pn in n or n in pn:
            return True
    return False

# ── Supabase ────────────────────────────────────────────────

def obtener_usuario_sistema():
    try:
        r = db.from_('usuarios').select('id').eq('rol', 'admin').limit(1).execute()
        if r.data:
            return r.data[0]['id']
    except Exception as e:
        log(f'ERROR consultando usuario admin: {e}')
    log('ERROR: No hay usuario admin. Registrate y ejecutá el UPDATE de admin.')
    sys.exit(1)

# ── Descarga ────────────────────────────────────────────────

def obtener_url_hoy():
    ahora_ar = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    dia = ahora_ar.weekday()
    url = SEPA_URLS[dia]
    log(f'Fecha AR: {ahora_ar.strftime("%Y-%m-%d %H:%M")} — dia {dia}')
    log(f'URL: {url}')
    return url

def descargar_zip(url):
    log('Descargando ZIP...')
    tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    try:
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            total = 0
            for chunk in r.iter_content(chunk_size=65536):
                tmp.write(chunk)
                total += len(chunk)
                if total % (50 * 1024 * 1024) == 0:
                    log(f'  {total // (1024*1024)} MB descargados...')
        tmp.close()
        log(f'ZIP descargado: {total // (1024*1024)} MB')
        return tmp.name
    except Exception as e:
        tmp.close()
        try: os.unlink(tmp.name)
        except Exception: pass
        log(f'ERROR descargando ZIP: {e}')
        sys.exit(1)

# ── Procesamiento ───────────────────────────────────────────

def leer_csv_bytes(zf, nombre_archivo):
    """Lee un archivo del ZIP y retorna sus bytes. Retorna None si no existe."""
    try:
        with zf.open(nombre_archivo) as f:
            return f.read()
    except KeyError:
        return None

def buscar_archivo_ci(zf, nombre_buscado):
    """Busca un archivo en el ZIP sin importar mayúsculas/minúsculas."""
    nombre_lower = nombre_buscado.lower()
    for nombre in zf.namelist():
        if nombre.lower() == nombre_lower or nombre.lower().endswith('/' + nombre_lower):
            return nombre
    return None

def leer_banderas(zf_inner):
    """
    Lee comercio.csv y retorna dict {id_bandera: nombre_bandera}.
    """
    nombre = buscar_archivo_ci(zf_inner, 'comercio.csv')
    if not nombre:
        return {}
    contenido = leer_csv_bytes(zf_inner, nombre)
    if not contenido:
        return {}
    try:
        wrapper = TextIOWrapper(io.BytesIO(contenido), encoding='utf-8', errors='replace')
        reader = csv.DictReader(wrapper, delimiter='|')
        banderas = {}
        for row in reader:
            bid = (row.get('id_bandera') or '').strip()
            bnombre = (row.get('comercio_bandera_nombre') or '').strip()
            if bid and bnombre:
                banderas[bid] = bnombre
        return banderas
    except Exception:
        return {}

def leer_sucursales(zf_inner):
    """
    Lee sucursales.csv y retorna dict {id_sucursal: provincia}.
    Usado para filtrar por provincia cuando productos.csv no tiene id_provincia.
    """
    nombre = buscar_archivo_ci(zf_inner, 'sucursales.csv')
    if not nombre:
        return {}
    contenido = leer_csv_bytes(zf_inner, nombre)
    if not contenido:
        return {}
    try:
        wrapper = TextIOWrapper(io.BytesIO(contenido), encoding='utf-8', errors='replace')
        reader = csv.DictReader(wrapper, delimiter='|')
        sucursales = {}
        for row in reader:
            sid = (row.get('id_sucursal') or '').strip()
            # Provincia puede venir como nombre o como código numérico
            prov = (row.get('provincia') or row.get('id_provincia') or '').strip()
            if sid:
                sucursales[sid] = prov
        return sucursales
    except Exception:
        return {}

def procesar_productos(zf_inner, banderas, sucursales, usuario_id, precios, es_debug):
    """
    Lee productos.csv y actualiza el dict de precios con los matcheos.
    """
    nombre = buscar_archivo_ci(zf_inner, 'productos.csv')
    if not nombre:
        if es_debug:
            log(f'  Sin productos.csv — archivos: {zf_inner.namelist()}')
        return 0

    contenido = leer_csv_bytes(zf_inner, nombre)
    if not contenido:
        return 0

    try:
        wrapper = TextIOWrapper(io.BytesIO(contenido), encoding='utf-8', errors='replace')
        reader = csv.DictReader(wrapper, delimiter='|')

        primera = next(iter(reader), None)
        if primera is None:
            return 0

        if es_debug:
            log(f'  Columnas productos.csv: {list(primera.keys())}')
            log(f'  Ejemplo: {dict(primera)}')

        filas = 0
        for row in [primera] + list(reader):
            filas += 1

            # Nombre de bandera — viene del id_bandera cruzado con comercio.csv
            id_bandera = (row.get('id_bandera') or '').strip()
            nombre_bandera = banderas.get(id_bandera, '')
            if not nombre_bandera:
                # Fallback: razón social si está en el mismo row
                nombre_bandera = (row.get('comercio_razon_social') or '').strip()

            cadena_id = detectar_cadena(nombre_bandera)
            if not cadena_id:
                continue

            # Provincia — puede venir en productos.csv o hay que cruzar con sucursales.csv
            prov_raw = (row.get('id_provincia') or row.get('provincia') or '').strip()
            if not prov_raw:
                id_suc = (row.get('id_sucursal') or '').strip()
                prov_raw = sucursales.get(id_suc, '')

            if not provincia_permitida(prov_raw):
                continue

            # Descripción del producto
            descripcion = (
                row.get('productos_descripcion') or
                row.get('nombre_producto') or
                row.get('descripcion') or ''
            ).strip()
            producto_id = detectar_producto(descripcion)
            if not producto_id:
                continue

            # Precio — usar precio_lista primero
            precio_raw = (
                row.get('precio_lista') or
                row.get('precio_unitario_bulto_por_unidad_venta_con_iva') or
                row.get('precio_referencia') or
                row.get('precio_unitario') or
                row.get('precio') or ''
            )
            precio = parsear_precio(precio_raw)
            if precio is None:
                continue

            # Guardar precio más bajo por producto+cadena
            key = (producto_id, cadena_id)
            if key not in precios or precio < precios[key]['precio']:
                precios[key] = {
                    'producto_id': producto_id,
                    'comercio_id': cadena_id,
                    'usuario_id':  usuario_id,
                    'precio':      precio,
                    'moneda':      MONEDA,
                    'verificado':  True,
                }

        return filas

    except Exception as e:
        if es_debug:
            log(f'  ERROR procesando productos.csv: {e}')
        return 0

def procesar_zip(zip_path, usuario_id):
    precios = {}
    total_zips = 0
    total_filas = 0
    zips_sin_productos = 0

    log('Procesando ZIP del SEPA...')

    with zipfile.ZipFile(zip_path, 'r') as zf_outer:
        zips_internos = sorted([
            f for f in zf_outer.namelist()
            if f.lower().endswith('.zip') and not f.endswith('/')
        ])
        log(f'ZIPs internos: {len(zips_internos)}')

        if not zips_internos:
            log('ERROR: El ZIP externo no tiene ZIPs internos.')
            log(f'Contenido ZIP externo: {zf_outer.namelist()[:10]}')
            return []

        for idx, nombre_zip in enumerate(zips_internos):
            es_debug = (idx == 0)
            try:
                with zf_outer.open(nombre_zip) as zb:
                    datos = io.BytesIO(zb.read())

                with zipfile.ZipFile(datos, 'r') as zf_inner:
                    if es_debug:
                        log(f'Primer ZIP: {nombre_zip}')
                        log(f'Archivos: {zf_inner.namelist()}')

                    banderas   = leer_banderas(zf_inner)
                    sucursales = leer_sucursales(zf_inner)
                    filas      = procesar_productos(
                        zf_inner, banderas, sucursales,
                        usuario_id, precios, es_debug
                    )

                    if filas == 0:
                        zips_sin_productos += 1
                    else:
                        total_filas += filas

                total_zips += 1

                if idx > 0 and idx % 100 == 0:
                    log(f'Progreso: {idx+1}/{len(zips_internos)} — {len(precios)} precios')

            except zipfile.BadZipFile as e:
                if idx < 3:
                    log(f'ZIP corrupto {idx}: {e}')
                continue
            except Exception as e:
                if idx < 3:
                    log(f'Error ZIP {idx}: {e}')
                continue

    log(f'ZIPs procesados: {total_zips} — sin productos.csv: {zips_sin_productos}')
    log(f'Filas procesadas: {total_filas:,} — Precios a insertar: {len(precios)}')

    if len(precios) == 0:
        log('AVISO: 0 precios encontrados.')
        log('Posibles causas:')
        log('  1. Los nombres de cadena en config_sepa.py no coinciden con comercio_bandera_nombre del SEPA')
        log('  2. Las keywords de productos no coinciden con productos_descripcion del SEPA')
        log('  3. El ZIP del dia solo tiene comercio.csv (raro pero posible)')
        log('Revisar el log de "Columnas productos.csv" y "Ejemplo" arriba para ajustar.')

    return list(precios.values())

# ── Inserción ───────────────────────────────────────────────

def insertar_precios(precios):
    if not precios:
        log('Sin precios para insertar')
        return

    cadena_ids = list(set(p['comercio_id'] for p in precios))
    log(f'Reemplazando precios anteriores de: {cadena_ids}')
    try:
        db.from_('precios').delete() \
            .in_('comercio_id', cadena_ids) \
            .eq('verificado', True) \
            .execute()
    except Exception as e:
        log(f'Warning al borrar anteriores: {e}')

    log(f'Insertando {len(precios)} precios...')
    insertados = 0
    for i in range(0, len(precios), 50):
        lote = precios[i:i+50]
        try:
            db.from_('precios').insert(lote).execute()
            insertados += len(lote)
        except Exception as e:
            log(f'Error lote {i//50+1}: {e}')

    log(f'Insertados: {insertados}/{len(precios)}')

# ── Main ─────────────────────────────────────────────────────

def main():
    log('=== Importador SEPA — PrecioVista ===')
    log(f'UTC: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')

    usuario_id = obtener_usuario_sistema()
    log(f'Admin: {usuario_id}')

    url      = obtener_url_hoy()
    zip_path = descargar_zip(url)

    try:
        precios = procesar_zip(zip_path, usuario_id)
        insertar_precios(precios)
        log('=== Importacion completada ===')
    except Exception as e:
        import traceback
        log(f'ERROR CRITICO: {e}')
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            os.unlink(zip_path)
            log('Temporal eliminado')
        except Exception:
            pass

if __name__ == '__main__':
    main()
