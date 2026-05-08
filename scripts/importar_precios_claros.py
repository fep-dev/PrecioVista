#!/usr/bin/env python3
# ============================================================
# importar_precios_claros.py — Importador diario via API Precios Claros
# PrecioVista © 2026 — CC BY-NC-SA 4.0
# ============================================================
# API endpoints oficiales de preciosclaros.gob.ar:
#   Sucursales: https://d3e6htiiul5ek9.cloudfront.net/prod/sucursales
#               ?lat=LAT&lng=LNG&limit=3000
#   Producto:   https://d3e6htiiul5ek9.cloudfront.net/prod/producto
#               ?limit=50&id_producto=ID&array_sucursales=ID1,ID2,...
# ============================================================

import os, sys, time, datetime, json, re
import requests
from supabase import create_client

sys.path.insert(0, os.path.dirname(__file__))
from config_precios_claros import (
    PRODUCTOS_API, CADENAS, PROVINCIAS_COORDS, MONEDA
)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('ERROR: Faltan variables de entorno SUPABASE_URL y SUPABASE_SERVICE_KEY')
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_URL = 'https://d3e6htiiul5ek9.cloudfront.net/prod'
HEADERS  = {
    'User-Agent': 'Mozilla/5.0 (compatible; PrecioVista/1.0)',
    'Accept':     'application/json',
}

def log(msg):
    print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}', flush=True)

# ── Supabase ────────────────────────────────────────────────

def obtener_usuario_sistema():
    try:
        r = db.from_('usuarios').select('id').eq('rol','admin').limit(1).execute()
        if r.data:
            return r.data[0]['id']
    except Exception as e:
        log(f'ERROR usuario admin: {e}')
    log('ERROR: No hay usuario admin.')
    sys.exit(1)

# ── Helpers ─────────────────────────────────────────────────

def normalizar(texto):
    if not texto: return ''
    t = str(texto).lower().strip()
    for c,s in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ñ','n')]:
        t = t.replace(c,s)
    return ' '.join(t.split())

def detectar_cadena_por_nombre(nombre_comercio):
    """Detecta la cadena por el nombre comercial usando word boundary."""
    n = normalizar(nombre_comercio)
    if not n: return None
    for cid, nombres in CADENAS.items():
        for nombre in nombres:
            if re.search(r'\b' + re.escape(normalizar(nombre)) + r'\b', n):
                return cid
    return None

def api_get(url, params=None, reintentos=3):
    """GET con reintentos y delay entre llamadas."""
    for intento in range(reintentos):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                # Rate limit — esperar más
                time.sleep(5 * (intento + 1))
                continue
            else:
                log(f'HTTP {r.status_code} en {url}')
                return None
        except requests.exceptions.Timeout:
            log(f'Timeout en intento {intento+1}')
            time.sleep(2)
        except Exception as e:
            log(f'Error request: {e}')
            time.sleep(2)
    return None

# ── Obtener sucursales ───────────────────────────────────────

def obtener_sucursales_provincia(nombre_provincia, lat, lng):
    """
    Obtiene sucursales cercanas a las coordenadas de la provincia.
    Filtra solo las cadenas configuradas.
    """
    log(f'Buscando sucursales en {nombre_provincia} ({lat},{lng})...')
    data = api_get(f'{BASE_URL}/sucursales', {
        'lat':   lat,
        'lng':   lng,
        'limit': 3000,
    })
    if not data or 'sucursales' not in data:
        log(f'Sin sucursales para {nombre_provincia}')
        return []

    sucursales = data['sucursales']
    log(f'  {len(sucursales)} sucursales encontradas en {nombre_provincia}')

    # Filtrar solo cadenas configuradas
    resultado = []
    for s in sucursales:
        nombre_comercio = s.get('comercioRazonSocial','') or s.get('banderaDescripcion','')
        cadena_id = detectar_cadena_por_nombre(nombre_comercio)
        if cadena_id:
            resultado.append({
                'id':       s.get('id',''),
                'nombre':   nombre_comercio,
                'cadena_id': cadena_id,
                'provincia': nombre_provincia,
            })

    log(f'  {len(resultado)} sucursales de cadenas configuradas')
    return resultado

# ── Obtener precios ──────────────────────────────────────────

def obtener_precios_producto(producto_id_api, sucursal_ids):
    """
    Obtiene precios de un producto en un lote de sucursales.
    La API acepta hasta 50 sucursales por request.
    """
    if not sucursal_ids:
        return []

    # La API acepta lista de IDs separados por coma
    array_suc = ','.join(sucursal_ids[:50])
    data = api_get(f'{BASE_URL}/producto', {
        'limit':           50,
        'id_producto':     producto_id_api,
        'array_sucursales': array_suc,
    })
    time.sleep(0.5)  # Rate limiting

    if not data or 'productos' not in data:
        return []

    return data['productos']

# ── Procesamiento principal ──────────────────────────────────

def importar_precios(usuario_id):
    precios_resultado = {}  # key: (producto_id_pv, cadena_id) → precio mínimo
    total_requests = 0

    for nombre_provincia, coords in PROVINCIAS_COORDS.items():
        lat, lng = coords
        log(f'\n=== Provincia: {nombre_provincia} ===')

        # 1. Obtener sucursales de la provincia
        sucursales = obtener_sucursales_provincia(nombre_provincia, lat, lng)
        if not sucursales:
            continue

        # Agrupar sucursales por cadena
        por_cadena = {}
        for s in sucursales:
            cid = s['cadena_id']
            if cid not in por_cadena:
                por_cadena[cid] = []
            por_cadena[cid].append(s['id'])

        # 2. Para cada producto configurado, obtener precios
        for producto_pv_id, config in PRODUCTOS_API.items():
            id_api     = config['id_api']
            nombre_log = config['nombre']

            # Procesar en lotes de 50 sucursales
            todos_ids = [s['id'] for s in sucursales]
            encontrados = 0

            for i in range(0, len(todos_ids), 50):
                lote = todos_ids[i:i+50]
                productos_api = obtener_precios_producto(id_api, lote)
                total_requests += 1

                for p in productos_api:
                    precio_lista = p.get('precioLista') or p.get('precio')
                    if not precio_lista:
                        continue
                    try:
                        precio = round(float(precio_lista), 2)
                        if precio <= 0:
                            continue
                    except (ValueError, TypeError):
                        continue

                    # Identificar cadena por sucursal
                    suc_id = str(p.get('sucursalId','') or p.get('id',''))
                    # Buscar en sucursales que tenemos
                    cadena_id = None
                    for s in sucursales:
                        if str(s['id']) == suc_id:
                            cadena_id = s['cadena_id']
                            break

                    if not cadena_id:
                        # Intentar por nombre del comercio en la respuesta
                        nombre_c = p.get('comercioRazonSocial','') or p.get('banderaDescripcion','')
                        cadena_id = detectar_cadena_por_nombre(nombre_c)

                    if not cadena_id:
                        continue

                    key = (producto_pv_id, cadena_id)
                    if key not in precios_resultado or precio < precios_resultado[key]['precio']:
                        precios_resultado[key] = {
                            'producto_id': producto_pv_id,
                            'comercio_id': cadena_id,
                            'usuario_id':  usuario_id,
                            'precio':      precio,
                            'moneda':      MONEDA,
                            'verificado':  True,
                        }
                        encontrados += 1

            if encontrados > 0:
                log(f'  {nombre_log}: {encontrados} precios encontrados')

    log(f'\nTotal requests API: {total_requests}')
    log(f'Total precios únicos: {len(precios_resultado)}')
    return list(precios_resultado.values())

# ── Inserción ────────────────────────────────────────────────

def insertar_precios(precios):
    if not precios:
        log('Sin precios para insertar')
        return

    cadena_ids = list(set(p['comercio_id'] for p in precios))
    log(f'Reemplazando precios de {len(cadena_ids)} cadenas...')
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
    log('=== Importador Precios Claros — PrecioVista ===')
    log(f'UTC: {datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
    usuario_id = obtener_usuario_sistema()
    log(f'Admin: {usuario_id}')
    try:
        precios = importar_precios(usuario_id)
        insertar_precios(precios)
        log('=== Importacion completada ===')
    except Exception as e:
        import traceback
        log(f'ERROR CRITICO: {e}')
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
