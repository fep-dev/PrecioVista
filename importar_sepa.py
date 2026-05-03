#!/usr/bin/env python3
# ============================================================
# importar_sepa.py — Importador diario de precios SEPA
# PrecioVista © 2026 — CC BY-NC-SA 4.0
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

def obtener_usuario_sistema():
    try:
        result = db.from_('usuarios').select('id').eq('rol', 'admin').limit(1).execute()
        if result.data:
            return result.data[0]['id']
    except Exception as e:
        log(f'ERROR consultando usuario admin: {e}')
    log('ERROR: No hay usuario admin en la base de datos')
    sys.exit(1)

def normalizar(texto):
    if not texto:
        return ''
    return ' '.join(str(texto).lower().strip().split())

def detectar_producto(nombre):
    n = normalizar(nombre)
    if not n:
        return None
    for pid, kws in PRODUCTOS.items():
        for kw in kws:
            if kw.lower() in n:
                return pid
    return None

def detectar_cadena(nombre):
    """
    BUG 1 CORREGIDO: detección por palabras completas, no por substring.
    'dia' no debe matchear en 'diario', 'vea' no en 'vealthy', etc.
    Usa word boundary para coincidir solo con palabras completas.
    """
    n = normalizar(nombre)
    if not n:
        return None
    for cid, ns in CADENAS.items():
        for nombre_cadena in ns:
            # Buscar como palabra completa (con bordes de palabra)
            patron = r'\b' + re.escape(nombre_cadena.lower()) + r'\b'
            if re.search(patron, n):
                return cid
    return None

def quitar_tildes(texto):
    """Elimina tildes para comparación robusta."""
    reemplazos = {
        'á':'a','é':'e','í':'i','ó':'o','ú':'u',
        'à':'a','è':'e','ì':'i','ò':'o','ù':'u',
        'ä':'a','ë':'e','ï':'i','ö':'o','ü':'u',
        'ñ':'n','ü':'u',
    }
    return ''.join(reemplazos.get(c, c) for c in texto)

def provincia_permitida(prov):
    """
    Verifica si la provincia está en el filtro.
    Maneja variantes de CABA y diferencias de tildes.
    """
    if not PROVINCIAS_FILTRO:
        return True
    n = quitar_tildes(normalizar(prov))
    if not n:
        return False
    # Normalizar variantes conocidas del SEPA
    n = n.replace('ciudad autonoma de buenos aires', 'ciudad de buenos aires')
    n = n.replace('caba', 'ciudad de buenos aires')
    for p in PROVINCIAS_FILTRO:
        p_norm = quitar_tildes(normalizar(p)).replace('ciudad autonoma de buenos aires', 'ciudad de buenos aires')
        if p_norm in n or n in p_norm:
            return True
    return False

def obtener_url_hoy():
    # Usar hora Argentina (UTC-3) para determinar el día correcto
    ahora_ar = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    dia = ahora_ar.weekday()
    url = SEPA_URLS[dia]
    log(f'Fecha Argentina: {ahora_ar.strftime("%Y-%m-%d")} — Dia {dia} — URL: {url}')
    return url

def parsear_precio(raw):
    """
    BUG 3 CORREGIDO: el formato argentino usa punto como separador de miles
    y coma como separador decimal. Ej: '1.250,50' debe convertirse en 1250.50.
    El método anterior hacía replace(',','.') dando '1.250.50' = 1.25 (INCORRECTO).
    """
    if not raw:
        return None
    try:
        texto = str(raw).strip()
        # Si tiene punto Y coma: formato argentino 1.250,50
        if ',' in texto and '.' in texto:
            texto = texto.replace('.', '').replace(',', '.')
        # Solo coma: puede ser decimal europeo 1250,50
        elif ',' in texto:
            texto = texto.replace(',', '.')
        # Solo punto: decimal estándar 1250.50 — no tocar
        precio = float(texto)
        return precio if precio > 0 else None
    except (ValueError, TypeError):
        return None

def tiene_columnas_precios(cols):
    """Verifica si un CSV contiene datos de precios (no solo de comercios)."""
    cl = [c.lower() for c in cols]
    return (
        any('precio' in c for c in cl) or
        any('nombre_producto' in c for c in cl) or
        any('id_producto' in c for c in cl)
    )

def _fila(row, precios, usuario_id):
    """Procesa una fila del CSV."""
    prov = (row.get('id_provincia') or row.get('provincia') or '').strip()
    if prov and not provincia_permitida(prov):
        return

    prod = (row.get('nombre_producto') or row.get('producto') or '').strip()
    pid = detectar_producto(prod)
    if not pid:
        return

    # El SEPA usa 'comercio_bandera_nombre' para el nombre comercial
    cadena = (
        row.get('comercio_bandera_nombre') or
        row.get('comercio_razon_social') or
        row.get('cadena') or ''
    ).strip()
    cid = detectar_cadena(cadena)
    if not cid:
        return

    precio = parsear_precio(row.get('precio') or row.get('precio_unitario'))
    if precio is None:
        return

    key = (pid, cid)
    if key not in precios or precio < precios[key]['precio']:
        precios[key] = {
            'producto_id': pid,
            'comercio_id': cid,
            'usuario_id':  usuario_id,
            'precio':      round(precio, 2),
            'moneda':      MONEDA,
            'verificado':  True,
        }

def descargar_zip(url):
    log('Descargando ZIP...')
    tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    try:
        # BUG 4 CORREGIDO: timeout aumentado a 600s para archivos grandes
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            total = 0
            for chunk in r.iter_content(chunk_size=65536):
                tmp.write(chunk)
                total += len(chunk)
                if total % (50 * 1024 * 1024) == 0:
                    log(f'  Descargado: {total // (1024*1024)} MB')
        tmp.close()
        log(f'ZIP descargado: {total // (1024*1024)} MB')
        return tmp.name
    except Exception as e:
        tmp.close()
        try:
            os.unlink(tmp.name)
        except:
            pass
        log(f'ERROR descargando ZIP: {e}')
        sys.exit(1)

def procesar_zip(zip_path, usuario_id):
    """
    BUG 5 CORREGIDO: función leer_csv_desde_zip_interno eliminada
    (era código muerto con bug de file handle cerrado).
    Todo el procesamiento es inline con context managers correctos.
    """
    precios = {}
    procesados = 0
    debug_hecho = False

    log('Procesando ZIP del SEPA...')

    with zipfile.ZipFile(zip_path, 'r') as zf_outer:
        zips_internos = [f for f in zf_outer.namelist() if f.lower().endswith('.zip')]
        log(f'ZIPs internos encontrados: {len(zips_internos)}')

        if not zips_internos:
            log('ERROR: No se encontraron ZIPs internos')
            return []

        for idx, zip_interno in enumerate(zips_internos):
            try:
                with zf_outer.open(zip_interno) as zb:
                    zf_data = io.BytesIO(zb.read())

                with zipfile.ZipFile(zf_data, 'r') as zf_inner:
                    archivos = [f for f in zf_inner.namelist() if not f.endswith('/')]

                    if not debug_hecho:
                        log(f'Primer ZIP interno: {zip_interno}')
                        log(f'Archivos dentro: {archivos}')

                    for arch in archivos:
                        try:
                            # Leer en memoria para evitar bug de file handle cerrado
                            with zf_inner.open(arch) as f:
                                contenido = f.read()

                            wrapper = TextIOWrapper(
                                io.BytesIO(contenido),
                                encoding='utf-8',
                                errors='replace'
                            )
                            reader = csv.DictReader(wrapper, delimiter='|')
                            primera = next(iter(reader), None)
                            if primera is None:
                                continue

                            cols = list(primera.keys())
                            if not debug_hecho:
                                log(f'  Archivo: {arch}')
                                log(f'  Columnas: {cols}')
                                log(f'  Primera fila: {dict(primera)}')

                            if not tiene_columnas_precios(cols):
                                if not debug_hecho:
                                    log(f'  => Sin columnas de precios, salteando')
                                continue

                            if not debug_hecho:
                                log(f'  => Archivo de precios encontrado')

                            # Procesar todas las filas
                            procesados += 1
                            _fila(primera, precios, usuario_id)
                            for row in reader:
                                procesados += 1
                                _fila(row, precios, usuario_id)
                            break

                        except Exception as e:
                            if not debug_hecho:
                                log(f'  Error en {arch}: {e}')
                            continue

                    debug_hecho = True

                    if idx > 0 and idx % 50 == 0:
                        log(f'Progreso: {idx}/{len(zips_internos)} — {procesados:,} filas — {len(precios)} precios')

            except Exception as e:
                if idx < 3:
                    log(f'Error ZIP {idx}: {e}')
                continue

    log(f'Total: {procesados:,} filas procesadas — {len(precios)} precios a insertar')
    return list(precios.values())

def insertar_precios(precios):
    if not precios:
        log('Sin precios para insertar')
        return

    cadena_ids = list(set(p['comercio_id'] for p in precios))
    log(f'Eliminando precios anteriores de {len(cadena_ids)} cadenas...')
    try:
        db.from_('precios').delete().in_('comercio_id', cadena_ids).eq('verificado', True).execute()
    except Exception as e:
        log(f'Warning al eliminar precios anteriores: {e}')

    log(f'Insertando {len(precios)} precios...')
    insertados = 0
    for i in range(0, len(precios), 50):
        lote = precios[i:i+50]
        try:
            db.from_('precios').insert(lote).execute()
            insertados += len(lote)
        except Exception as e:
            log(f'Error en lote {i//50 + 1}: {e}')

    log(f'Insertados: {insertados}/{len(precios)} precios')

def main():
    log('=== Importador SEPA — PrecioVista ===')
    log(f'Fecha UTC: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
    usuario_id = obtener_usuario_sistema()
    log(f'Usuario admin: {usuario_id}')
    url = obtener_url_hoy()
    zip_path = descargar_zip(url)
    try:
        precios = procesar_zip(zip_path, usuario_id)
        insertar_precios(precios)
        log('=== Importacion completada ===')
    except Exception as e:
        log(f'ERROR CRITICO: {e}')
        sys.exit(1)
    finally:
        try:
            os.unlink(zip_path)
            log('Archivo temporal eliminado')
        except:
            pass

if __name__ == '__main__':
    main()
