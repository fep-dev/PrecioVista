#!/usr/bin/env python3
# ============================================================
# importar_sepa.py — Importador diario de precios SEPA
# PrecioVista © 2026 — CC BY-NC-SA 4.0
# ============================================================
# Este script:
# 1. Descarga el ZIP del día desde datos.gob.ar
# 2. Procesa el CSV línea por línea (sin cargar todo en memoria)
# 3. Filtra solo los productos y cadenas configurados
# 4. Inserta los precios en Supabase con verificado=true
# ============================================================

import os
import sys
import csv
import zipfile
import requests
import tempfile
import datetime
from io import TextIOWrapper
from supabase import create_client

# Importar configuración
sys.path.insert(0, os.path.dirname(__file__))
from config_sepa import PRODUCTOS, CADENAS, PROVINCIAS_FILTRO, SEPA_URLS, MONEDA, MAX_REGISTROS_POR_COMBO

# ── Conexión Supabase ───────────────────────────────────────
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')  # Service key para bypass RLS

if not SUPABASE_URL or not SUPABASE_KEY:
    print('ERROR: Faltan variables de entorno SUPABASE_URL y SUPABASE_SERVICE_KEY')
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)

def log(msg):
    print(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}')

# ── Obtener usuario sistema ─────────────────────────────────
def obtener_usuario_sistema():
    """Obtiene el ID del usuario admin para atribuir los precios importados."""
    result = db.from_('usuarios').select('id').eq('rol', 'admin').limit(1).execute()
    if result.data:
        return result.data[0]['id']
    log('ERROR: No hay usuario admin en la base de datos')
    sys.exit(1)

# ── Normalizar texto ────────────────────────────────────────
def normalizar(texto):
    """Convierte a minúsculas y elimina espacios extra para comparar."""
    if not texto:
        return ''
    return ' '.join(texto.lower().strip().split())

# ── Detectar producto ───────────────────────────────────────
def detectar_producto(nombre_sepa):
    """Retorna el id del producto si el nombre matchea alguna palabra clave."""
    nombre_norm = normalizar(nombre_sepa)
    for producto_id, keywords in PRODUCTOS.items():
        for kw in keywords:
            if kw.lower() in nombre_norm:
                return producto_id
    return None

# ── Detectar cadena ─────────────────────────────────────────
def detectar_cadena(nombre_comercio):
    """Retorna el id de la cadena si el nombre matchea."""
    nombre_norm = normalizar(nombre_comercio)
    for cadena_id, nombres in CADENAS.items():
        for n in nombres:
            if n.lower() in nombre_norm:
                return cadena_id
    return None

# ── Detectar provincia ──────────────────────────────────────
def provincia_permitida(nombre_provincia):
    """Verifica si la provincia está en el filtro configurado."""
    if not PROVINCIAS_FILTRO:
        return True  # Sin filtro — importar todas
    nombre_norm = normalizar(nombre_provincia)
    for p in PROVINCIAS_FILTRO:
        if normalizar(p) in nombre_norm or nombre_norm in normalizar(p):
            return True
    return False

# ── Obtener URL del día ─────────────────────────────────────
def obtener_url_hoy():
    """Retorna la URL del ZIP del día actual."""
    dia = datetime.datetime.now().weekday()  # 0=lunes, 6=domingo
    url = SEPA_URLS[dia]
    log(f'Día de la semana: {dia} — URL: {url}')
    return url

# ── Descargar ZIP ───────────────────────────────────────────
def descargar_zip(url):
    """Descarga el ZIP a un archivo temporal."""
    log(f'Descargando ZIP...')
    tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = 0
        for chunk in r.iter_content(chunk_size=8192):
            tmp.write(chunk)
            total += len(chunk)
            if total % (10 * 1024 * 1024) == 0:
                log(f'  Descargado: {total // (1024*1024)} MB')
    tmp.close()
    log(f'ZIP descargado: {total // (1024*1024)} MB')
    return tmp.name

# ── Procesar CSV ────────────────────────────────────────────
def procesar_csv(zip_path, usuario_id):
    """
    Procesa el CSV línea por línea para no cargar 12M de registros en memoria.
    Retorna lista de precios a insertar.
    """
    precios = {}  # key: (producto_id, cadena_id) → precio más bajo encontrado
    procesados = 0
    matcheados = 0

    log('Procesando CSV...')

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # El ZIP contiene un CSV — buscar el archivo
        csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
        if not csv_files:
            log('ERROR: No se encontró CSV en el ZIP')
            return []

        csv_file = csv_files[0]
        log(f'Archivo CSV: {csv_file}')

        with zf.open(csv_file) as f:
            reader = csv.DictReader(
                TextIOWrapper(f, encoding='utf-8', errors='replace'),
                delimiter='|'  # El SEPA usa | como separador
            )

            for row in reader:
                procesados += 1

                # Log de progreso cada 500k registros
                if procesados % 500000 == 0:
                    log(f'  Procesados: {procesados:,} — Matcheados: {matcheados}')

                # Verificar provincia
                provincia = row.get('id_provincia', '') or row.get('provincia', '')
                if not provincia_permitida(provincia):
                    continue

                # Verificar producto
                nombre_prod = row.get('nombre_producto', '') or row.get('producto', '')
                producto_id = detectar_producto(nombre_prod)
                if not producto_id:
                    continue

                # Verificar cadena
                nombre_comercio = row.get('comercio_razon_social', '') or row.get('cadena', '')
                cadena_id = detectar_cadena(nombre_comercio)
                if not cadena_id:
                    continue

                # Obtener precio
                try:
                    precio_str = row.get('precio', '0').replace(',', '.')
                    precio = float(precio_str)
                    if precio <= 0:
                        continue
                except (ValueError, TypeError):
                    continue

                # Guardar el precio más bajo por combo producto+cadena
                key = (producto_id, cadena_id)
                if key not in precios or precio < precios[key]['precio']:
                    precios[key] = {
                        'producto_id':  producto_id,
                        'comercio_id':  cadena_id,
                        'usuario_id':   usuario_id,
                        'precio':       precio,
                        'moneda':       MONEDA,
                        'verificado':   True,
                    }
                    matcheados = len(precios)

    log(f'CSV procesado: {procesados:,} registros — {matcheados} precios a insertar')
    return list(precios.values())

# ── Insertar en Supabase ────────────────────────────────────
def insertar_precios(precios):
    """Inserta los precios en Supabase en lotes de 100."""
    if not precios:
        log('Sin precios para insertar')
        return

    # Primero borrar los precios automáticos del día anterior
    log('Eliminando precios anteriores importados automáticamente...')
    # Solo borramos los precios verificados que fueron importados
    # (identificados por pertenecer a las cadenas configuradas)
    cadena_ids = list(set([p['comercio_id'] for p in precios]))
    db.from_('precios')\
        .delete()\
        .in_('comercio_id', cadena_ids)\
        .eq('verificado', True)\
        .execute()

    # Insertar en lotes
    log(f'Insertando {len(precios)} precios...')
    lote_size = 100
    insertados = 0

    for i in range(0, len(precios), lote_size):
        lote = precios[i:i + lote_size]
        try:
            db.from_('precios').insert(lote).execute()
            insertados += len(lote)
        except Exception as e:
            log(f'Error en lote {i//lote_size + 1}: {e}')

    log(f'Insertados: {insertados}/{len(precios)} precios')

# ── Main ────────────────────────────────────────────────────
def main():
    log('=== Importador SEPA — PrecioVista ===')
    log(f'Fecha: {datetime.datetime.now().strftime("%Y-%m-%d")}')

    # 1. Obtener usuario sistema
    usuario_id = obtener_usuario_sistema()
    log(f'Usuario sistema: {usuario_id}')

    # 2. Descargar ZIP del día
    url = obtener_url_hoy()
    zip_path = descargar_zip(url)

    try:
        # 3. Procesar CSV
        precios = procesar_csv(zip_path, usuario_id)

        # 4. Insertar en Supabase
        insertar_precios(precios)

        log('=== Importación completada ===')

    finally:
        # Limpiar archivo temporal
        os.unlink(zip_path)
        log('Archivo temporal eliminado')

if __name__ == '__main__':
    main()
