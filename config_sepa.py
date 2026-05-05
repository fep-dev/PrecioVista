# ============================================================
# config_sepa.py — Configuración del importador SEPA
# ============================================================
# CÓMO MODIFICAR:
# - Para agregar un producto: agregá una entrada en PRODUCTOS
#   con las palabras clave que aparecen en productos_descripcion del SEPA
# - Para agregar una cadena: agregá una entrada en CADENAS
#   con el nombre que usa el campo comercio_bandera_nombre en el SEPA
# - Para cambiar provincias: modificá PROVINCIAS_FILTRO
#   (dejarlo vacío [] importa todo el país)
# ============================================================

# ── Productos ───────────────────────────────────────────────
# Clave: id del producto en PrecioVista (debe existir en tabla productos)
# Valor: lista de palabras clave a buscar en productos_descripcion del SEPA
# Las keywords se normalizan (sin tildes, minúsculas) antes de comparar

PRODUCTOS = {
    'leche_1l': [
        'leche entera 1l',
        'leche entera 1 l',
        'leche entera 1lt',
        'leche entera 1 lt',
        'leche entera sachet 1',
    ],
    'pan_lactal': [
        'pan lactal',
        'pan de miga',
        'pan blanco lactal',
    ],
    'aceite_900ml': [
        'aceite girasol 900',
        'aceite de girasol 900',
        'aceite girasol 0.9',
    ],
    'arroz_1kg': [
        'arroz largo fino 1kg',
        'arroz largo fino 1 kg',
        'arroz largo 1kg',
        'arroz largo 1 kg',
    ],
    'azucar_1kg': [
        'azucar comun 1kg',
        'azucar comun 1 kg',
        'azucar 1kg',
        'azucar 1 kg',
    ],
    'coca_2l': [
        'coca-cola 2.25',
        'coca cola 2.25',
        'coca-cola 2,25',
        'cola 2.25l',
    ],
    'yerba_500g': [
        'yerba mate 500g',
        'yerba mate 500 g',
        'yerba mate 0.5kg',
    ],
    'harina_1kg': [
        'harina 0000 1kg',
        'harina 0000 1 kg',
        'harina 000 1kg',
        'harina comun 1kg',
    ],
    'fideos_500g': [
        'fideos tallarin 500',
        'fideos tallarines 500',
        'fideos 500g',
        'fideos 500 g',
    ],
    'huevos_12': [
        'huevos blancos x12',
        'huevos x12',
        'huevos x 12',
        'huevos docena',
        'huevos blancos docena',
    ],
}

# ── Cadenas ─────────────────────────────────────────────────
# Clave: id de la cadena en PrecioVista (debe existir en tabla comercios)
# Valor: lista de nombres a buscar en comercio_bandera_nombre del SEPA
# IMPORTANTE: usar nombres exactos como aparecen en el SEPA
# Se usan word boundaries — 'dia' NO matchea 'diario'

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

# ── Provincias a importar ────────────────────────────────────
# Dejá [] para importar todo el país
# Las comparaciones ignoran tildes automáticamente
PROVINCIAS_FILTRO = [
    'Ciudad de Buenos Aires',
    'Buenos Aires',
    'Cordoba',
    'Santa Fe',
    'Mendoza',
]

# ── URLs del SEPA por día ────────────────────────────────────
# No modificar — URLs oficiales de datos.produccion.gob.ar
SEPA_URLS = {
    0: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/0a9069a9-06e8-4f98-874d-da5578693290/download/sepa_lunes.zip',
    1: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/9dc06241-cc83-44f4-8e25-c9b1636b8bc8/download/sepa_martes.zip',
    2: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/1e92cd42-4f94-4071-a165-62c4cb2ce23c/download/sepa_miercoles.zip',
    3: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/d076720f-a7f0-4af8-b1d6-1b99d5a90c14/download/sepa_jueves.zip',
    4: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/91bc072a-4726-44a1-85ec-4a8467aad27e/download/sepa_viernes.zip',
    5: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/b3c3da5d-213d-41e7-8d74-f23fda0a3c30/download/sepa_sabado.zip',
    6: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/f8e75128-515a-436e-bf8d-5c63a62f2005/download/sepa_domingo.zip',
}

# ── Moneda ───────────────────────────────────────────────────
MONEDA = 'ARS'
