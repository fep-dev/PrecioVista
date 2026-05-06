#!/usr/bin/env python3
# ============================================================
# importar_sepa.py — Importador diario de precios SEPA
# PrecioVista © 2026 — CC BY-NC-SA 4.0
# ============================================================
# Estructura SEPA (Anexo II Res. N° 678/2020):
# ZIP externo → N ZIPs internos por comercio
# Nombre ZIP: sepa_1_comercio-sepa-XX_FECHA.zip → comercio.csv + sucursales.csv
#             sepa_2_comercio-sepa-XX_FECHA.zip → productos.csv (con precios)
#
# Columnas productos.csv (separador |, decimal punto):
#   id_comercio | id_bandera | id_sucursal | id_producto | productos_ean |
#   productos_descripcion | productos_cantidad_presentacion |
#   productos_unidad_medida_presentacion | productos_marca |
#   productos_precio_lista | productos_precio_referencia |
#   productos_cantidad_referencia | productos_unidad_medida_referencia |
#   productos_precio_unitario_promo1 | productos_leyenda_promo1 |
#   productos_precio_unitario_promo2 | productos_leyenda_promo2
# ============================================================

import os, sys, csv, zipfile, requests, tempfile, datetime, io, re
from io import TextIOWrapper
from supabase import create_client

sys.path.insert(0, os.path.dirname(__file__))
from config_sepa import PRODUCTOS, CADENAS, PROVINCIAS_FILTRO, SEPA_URLS, MONEDA

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
    """Busca cadena con word boundary para evitar falsos positivos."""
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
    Según documentación oficial el precio usa punto como decimal.
    Ej: '111.66', '1250.00'
    Manejamos también coma por si algún comercio no cumple el estándar.
    """
    if not raw:
        return None
    try:
        t = str(raw).strip()
        if not t or t in ('0', '0.0', '0.00', '0,0', '0,00'):
            return None
        # Formato argentino no estándar: 1.250,50
        if ',' in t and '.' in t:
            t = t.replace('.', '').replace(',', '.')
        # Solo coma: 1250,50
        elif ',' in t:
            t = t.replace(',', '.')
        # Estándar con punto: 1250.50 — no tocar
        precio = float(t)
        return round(precio, 2) if precio > 0 else None
    except (ValueError, TypeError):
        return None

def provincia_permitida(codigo_provincia):
    """
    sucursales.csv usa código ISO 3166-2 para provincia.
    Ej: AR-B=Buenos Aires, AR-C=CABA, AR-X=Córdoba, AR-S=Santa Fe, AR-M=Mendoza
    """
    if not PROVINCIAS_FILTRO:
        return True
    if not codigo_provincia:
        return True  # sin datos de provincia = aceptar
    # Mapeo de códigos ISO a nombres normalizados
    CODIGOS_ISO = {
        'ar-b': 'buenos aires',
        'ar-c': 'ciudad de buenos aires',
        'ar-x': 'cordoba',
        'ar-s': 'santa fe',
        'ar-m': 'mendoza',
        'ar-h': 'chaco',
        'ar-u': 'chubut',
        'ar-e': 'entre rios',
        'ar-p': 'formosa',
        'ar-y': 'jujuy',
        'ar-l': 'la pampa',
        'ar-f': 'la rioja',
        'ar-n': 'misiones',
        'ar-q': 'neuquen',
        'ar-r': 'rio negro',
        'ar-a': 'salta',
        'ar-j': 'san juan',
        'ar-d': 'san luis',
        'ar-z': 'santa cruz',
        'ar-g': 'santiago del estero',
        'ar-v': 'tierra del fuego',
        'ar-t': 'tucuman',
        'ar-k': 'catamarca',
        'ar-w': 'corrientes',
    }
    codigo_lower = codigo_provincia.lower().strip()
    nombre_prov = CODIGOS_ISO.get(codigo_lower, normalizar(codigo_provincia))

    for p in PROVINCIAS_FILTRO:
        pn = normalizar(p).replace('ciudad autonoma de buenos aires', 'ciudad de buenos aires')
        if pn in nombre_prov or nombre_prov in pn:
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
    log('ERROR: No hay usuario admin.')
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
                    log(f'  {total // (1024*1024)} MB...')
        tmp.close()
        log(f'ZIP descargado: {total // (1024*1024)} MB')
        return tmp.name
    except Exception as e:
        tmp.close()
        try: os.unlink(tmp.name)
        except Exception: pass
        log(f'ERROR descargando: {e}')
        sys.exit(1)

# ── Procesamiento ───────────────────────────────────────────

def leer_csv_de_zip(zf_inner, nombre_archivo):
    """Lee un CSV del ZIP interno. Retorna (reader, primera_fila) o (None, None)."""
    # Buscar el archivo case-insensitive
    nombre_lower = nombre_archivo.lower()
    nombre_real = None
    for n in zf_inner.namelist():
        if n.lower() == nombre_lower or n.lower().endswith('/' + nombre_lower):
            nombre_real = n
            break
    if not nombre_real:
        return None, None
    try:
        with zf_inner.open(nombre_real) as f:
            contenido = f.read()
        wrapper = TextIOWrapper(io.BytesIO(contenido), encoding='utf-8', errors='replace')
        reader = csv.DictReader(wrapper, delimiter='|')
        primera = next(iter(reader), None)
        return reader, primera
    except Exception:
        return None, None

def construir_mapa_sucursales(zf_inner):
    """
    Lee sucursales.csv y construye dict {id_sucursal: codigo_provincia}.
    Necesario porque productos.csv no tiene provincia directamente.
    """
    reader, primera = leer_csv_de_zip(zf_inner, 'sucursales.csv')
    if primera is None:
        return {}
    sucursales = {}
    for row in [primera] + list(reader):
        sid   = (row.get('id_sucursal') or '').strip()
        prov  = (row.get('sucursales_provincia') or row.get('provincia') or '').strip()
        if sid:
            sucursales[sid] = prov
    return sucursales

def construir_mapa_banderas(zf_inner):
    """
    Lee comercio.csv y construye dict {id_bandera: nombre_bandera}.
    """
    reader, primera = leer_csv_de_zip(zf_inner, 'comercio.csv')
    if primera is None:
        return {}
    banderas = {}
    for row in [primera] + list(reader):
        bid    = (row.get('id_bandera') or '').strip()
        bnombre = (row.get('comercio_bandera_nombre') or '').strip()
        if bid and bnombre:
            banderas[bid] = bnombre
    return banderas

def es_zip_de_productos(nombre_zip):
    """
    Determina si un ZIP interno contiene productos (precios).
    Según el SEPA, los ZIPs de productos tienen 'sepa_2' en el nombre
    o contienen productos.csv.
    """
    n = nombre_zip.lower()
    return 'sepa_2' in n or 'productos' in n

def procesar_zip(zip_path, usuario_id):
    precios   = {}
    total_filas = 0
    debug_hecho = False

    log('Procesando ZIP del SEPA...')

    with zipfile.ZipFile(zip_path, 'r') as zf_outer:
        todos_los_zips = sorted([
            f for f in zf_outer.namelist()
            if f.lower().endswith('.zip') and not f.endswith('/')
        ])
        log(f'Total ZIPs internos: {len(todos_los_zips)}')

        if not todos_los_zips:
            log('ERROR: No hay ZIPs internos.')
            log(f'Contenido: {zf_outer.namelist()[:10]}')
            return []

        # Mostrar primeros nombres para diagnóstico
        log(f'Primeros 5 nombres: {todos_los_zips[:5]}')

        # Separar ZIPs de comercio (tipo 1) y de productos (tipo 2)
        zips_tipo1 = [z for z in todos_los_zips if 'sepa_1' in z.lower() or
                      ('sepa_2' not in z.lower() and 'producto' not in z.lower())]
        zips_tipo2 = [z for z in todos_los_zips if 'sepa_2' in z.lower() or
                      'producto' in z.lower()]

        log(f'ZIPs tipo 1 (comercio/sucursales): {len(zips_tipo1)}')
        log(f'ZIPs tipo 2 (productos/precios): {len(zips_tipo2)}')

        if not zips_tipo2:
            log('AVISO: No se encontraron ZIPs de productos (sepa_2).')
            log('Intentando procesar todos los ZIPs por si contienen productos.csv...')
            zips_tipo2 = todos_los_zips

        # No pre-cargamos banderas globales — cada ZIP interno tiene su propio
        # comercio.csv con id_bandera=1 que puede repetirse entre comercios.
        # Las banderas se cargan desde el mismo ZIP que los productos.

        # Procesar ZIPs de productos
        for idx, nombre_zip in enumerate(zips_tipo2):
            try:
                with zf_outer.open(nombre_zip) as zb:
                    datos = io.BytesIO(zb.read())

                with zipfile.ZipFile(datos, 'r') as zf_inner:
                    archivos = zf_inner.namelist()

                    if not debug_hecho:
                        log(f'Primer ZIP tipo 2: {nombre_zip}')
                        log(f'Archivos: {archivos}')

                    # Cargar banderas del MISMO ZIP — cada comercio tiene id_bandera=1
                    # No mezclar banderas entre ZIPs distintos
                    banderas = construir_mapa_banderas(zf_inner)

                    # Cargar sucursales para mapear provincia
                    sucursales = construir_mapa_sucursales(zf_inner)

                    # Leer productos.csv
                    reader, primera = leer_csv_de_zip(zf_inner, 'productos.csv')

                    if primera is None:
                        if not debug_hecho:
                            log(f'  Sin productos.csv — archivos: {archivos}')
                        debug_hecho = True
                        continue

                    if not debug_hecho:
                        log(f'Columnas productos.csv: {list(primera.keys())}')
                        log(f'Ejemplo fila: {dict(primera)}')

                    # Procesar filas
                    for row in [primera] + list(reader):
                        total_filas += 1

                        # Nombre de bandera
                        id_bandera = (row.get('id_bandera') or '').strip()
                        nombre_bandera = banderas.get(id_bandera, '')
                        cadena_id = detectar_cadena(nombre_bandera)
                        if not cadena_id:
                            continue

                        # Provincia via sucursal
                        id_suc = (row.get('id_sucursal') or '').strip()
                        cod_prov = sucursales.get(id_suc, '')
                        if not provincia_permitida(cod_prov):
                            continue

                        # Descripción del producto
                        desc = (row.get('productos_descripcion') or '').strip()
                        producto_id = detectar_producto(desc)
                        if not producto_id:
                            continue

                        # Precio lista (campo oficial según documentación)
                        precio = parsear_precio(row.get('productos_precio_lista'))
                        if precio is None:
                            continue

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

                    debug_hecho = True

                    if idx > 0 and idx % 100 == 0:
                        log(f'Progreso: {idx}/{len(zips_tipo2)} — {len(precios)} precios')

            except zipfile.BadZipFile:
                continue
            except Exception as e:
                if idx < 3:
                    log(f'Error ZIP {idx}: {e}')
                continue

    log(f'Filas procesadas: {total_filas:,} — Precios a insertar: {len(precios)}')

    if len(precios) == 0 and total_filas > 0:
        log('AVISO: Filas procesadas pero 0 precios. Causas posibles:')
        log('  1. Nombres de bandera en config_sepa.py no coinciden con comercio_bandera_nombre')
        log('  2. Keywords de productos no coinciden con productos_descripcion')
        log('  3. Todas las sucursales están en provincias no incluidas en PROVINCIAS_FILTRO')

    return list(precios.values())

# ── Inserción ───────────────────────────────────────────────

def insertar_precios(precios):
    if not precios:
        log('Sin precios para insertar')
        return

    cadena_ids = list(set(p['comercio_id'] for p in precios))
    log(f'Reemplazando precios anteriores...')
    try:
        db.from_('precios').delete() \
          .in_('comercio_id', cadena_ids) \
          .eq('verificado', True) \
          .execute()
    except Exception as e:
        log(f'Warning borrado: {e}')

    log(f'Insertando {len(precios)} precios...')
    insertados = 0
    for i in range(0, len(precios), 50):
        try:
            db.from_('precios').insert(precios[i:i+50]).execute()
            insertados += len(precios[i:i+50])
        except Exception as e:
            log(f'Error lote {i//50+1}: {e}')

    log(f'Insertados: {insertados}/{len(precios)}')

# ── Main ─────────────────────────────────────────────────────

def main():
    log('=== Importador SEPA — PrecioVista ===')
    log(f'UTC: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
    usuario_id = obtener_usuario_sistema()
    log(f'Admin: {usuario_id}')
    url = obtener_url_hoy()
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
