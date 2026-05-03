# ============================================================
# config_sepa.py — Configuración del importador SEPA
# ============================================================
# Este archivo es el único que necesitás modificar para:
# - Agregar nuevos productos
# - Agregar nuevas cadenas
# - Cambiar qué provincias importar
# ============================================================

# ── Productos a importar ────────────────────────────────────
# Formato: 'id_en_preciovista': ['palabra_clave_1', 'palabra_clave_2']
# El importador busca estas palabras en el nombre del producto del SEPA
# Si el nombre contiene CUALQUIERA de las palabras clave, se importa

PRODUCTOS = {
    'leche_1l':     ['leche entera 1l', 'leche entera 1 l', 'leche entera 1lt'],
    'pan_lactal':   ['pan lactal', 'pan de miga'],
    'aceite_900ml': ['aceite girasol 900', 'aceite de girasol 900'],
    'arroz_1kg':    ['arroz largo fino 1kg', 'arroz largo 1 kg', 'arroz largo 1kg'],
    'azucar_1kg':   ['azucar comun 1kg', 'azúcar común 1kg', 'azucar 1 kg'],
    'coca_2l':      ['coca-cola 2.25', 'coca cola 2.25', 'coca-cola 2,25'],
    'yerba_500g':   ['yerba mate 500g', 'yerba mate 500 g'],
    'harina_1kg':   ['harina 0000 1kg', 'harina 000 1kg', 'harina comun 1kg'],
    'fideos_500g':  ['fideos tallarin 500', 'fideos tallarín 500', 'fideos 500g'],
    'huevos_12':    ['huevos blancos x12', 'huevos x 12', 'huevos docena'],
}

# ── Cadenas a importar ──────────────────────────────────────
# Formato: 'id_en_preciovista': ['nombre_sepa_1', 'nombre_sepa_2']
# El SEPA usa nombres de cadena que pueden variar — agregá variantes si no matchea

CADENAS = {
    'carrefour_ar': ['carrefour'],
    'coto_ar':      ['coto'],
    'disco_ar':     ['disco'],
    'dia_ar':       ['dia', 'día'],
    'jumbo_ar':     ['jumbo'],
    'walmart_ar':   ['walmart', 'changomas', 'changomás'],
    'chango_ar':    ['changomas', 'changomás', 'chango mas'],
    'vea_ar':       ['vea'],
}

# ── Provincias a importar ───────────────────────────────────
# Dejá vacío [] para importar todas las provincias
# O listá solo las que querés: ['Buenos Aires', 'Córdoba', 'Santa Fe']
# Usar [] al principio para no sobrecargar Supabase

PROVINCIAS_FILTRO = [
    'Ciudad Autónoma de Buenos Aires',
    'Buenos Aires',
    'Córdoba',
    'Santa Fe',
    'Mendoza',
]

# ── URLs del SEPA por día de la semana ──────────────────────
# No modificar — se calculan automáticamente en el script

SEPA_URLS = {
    0: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/0a9069a9-06e8-4f98-874d-da5578693290/download/sepa_lunes.zip',
    1: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/9dc06241-cc83-44f4-8e25-c9b1636b8bc8/download/sepa_martes.zip',
    2: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/1e92cd42-4f94-4071-a165-62c4cb2ce23c/download/sepa_miercoles.zip',
    3: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/d076720f-a7f0-4af8-b1d6-1b99d5a90c14/download/sepa_jueves.zip',
    4: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/91bc072a-4726-44a1-85ec-4a8467aad27e/download/sepa_viernes.zip',
    5: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/b3c3da5d-213d-41e7-8d74-f23fda0a3c30/download/sepa_sabado.zip',
    6: 'https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/f8e75128-515a-436e-bf8d-5c63a62f2005/download/sepa_domingo.zip',
}

# ── Moneda ──────────────────────────────────────────────────
MONEDA = 'ARS'

# ── Límite de registros por producto por cadena ─────────────
# Para no sobrecargar Supabase — importa solo el precio más reciente
MAX_REGISTROS_POR_COMBO = 1
