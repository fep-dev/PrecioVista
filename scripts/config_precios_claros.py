# ============================================================
# config_precios_claros.py — Configuración importador API Precios Claros
# ============================================================
# CÓMO MODIFICAR:
# - Para agregar un producto: buscá su id_api en preciosclaros.gob.ar
#   (inspeccioná el network tab del navegador al buscar el producto)
# - Para agregar una cadena: agregá el nombre exacto que usa la API
# - Para agregar una provincia: agregá coordenadas del centro de la provincia
# ============================================================

# ── Productos ────────────────────────────────────────────────
# id_api: el EAN/GTIN del producto o su ID interno en Precios Claros
# Estos IDs los obtuviste inspeccionando la API del sitio

PRODUCTOS_API = {
    'leche_1l': {
        'id_api':  '7790070017241',  # Leche La Serenísima entera 1L
        'nombre':  'Leche entera 1L',
    },
    'pan_lactal': {
        'id_api':  '7790040016209',  # Pan Lactal Bimbo
        'nombre':  'Pan lactal',
    },
    'aceite_900ml': {
        'id_api':  '7790045000343',  # Aceite Cocinero girasol 900ml
        'nombre':  'Aceite girasol 900ml',
    },
    'arroz_1kg': {
        'id_api':  '7790070026779',  # Arroz Gallo Oro largo fino 1kg
        'nombre':  'Arroz largo 1kg',
    },
    'azucar_1kg': {
        'id_api':  '7790040055307',  # Azúcar Ledesma común 1kg
        'nombre':  'Azúcar 1kg',
    },
    'coca_2l': {
        'id_api':  '7790895000063',  # Coca-Cola 2.25L
        'nombre':  'Coca-Cola 2.25L',
    },
    'yerba_500g': {
        'id_api':  '7790387010104',  # Yerba Rosamonte 500g
        'nombre':  'Yerba mate 500g',
    },
    'harina_1kg': {
        'id_api':  '7790040007856',  # Harina Cañuelas 0000 1kg
        'nombre':  'Harina 0000 1kg',
    },
    'fideos_500g': {
        'id_api':  '7790040060189',  # Fideos Matarazzo tallarín 500g
        'nombre':  'Fideos tallarín 500g',
    },
    'huevos_12': {
        'id_api':  '7790625002052',  # Huevos Granja del Sol x12
        'nombre':  'Huevos x12',
    },
}

# ── Cadenas ──────────────────────────────────────────────────
# Nombres exactos como los devuelve la API de Precios Claros

CADENAS = {
    'carrefour_ar': ['carrefour'],
    'coto_ar':      ['coto'],
    'disco_ar':     ['disco'],
    'dia_ar':       ['dia', 'supermercados dia'],
    'jumbo_ar':     ['jumbo'],
    'walmart_ar':   ['walmart'],
    'chango_ar':    ['changomas', 'chango mas', 'chango+'],
    'vea_ar':       ['vea', 'supermercados vea'],
}

# ── Provincias con coordenadas ────────────────────────────────
# Coordenadas del centro de cada provincia para buscar sucursales
# La API devuelve hasta 3000 sucursales en un radio amplio

PROVINCIAS_COORDS = {
    'Ciudad de Buenos Aires': (-34.6037, -58.3816),
    'Buenos Aires':           (-36.6769, -60.5588),
    'Córdoba':                (-31.4135, -64.1811),
    'Santa Fe':               (-31.6107, -60.6971),
    'Mendoza':                (-32.8895, -68.8458),
}

# ── Moneda ───────────────────────────────────────────────────
MONEDA = 'ARS'
