// ============================================================
// PrecioVista — Datos: países, provincias, cadenas
// Copyright © 2026 PrecioVista. CC BY-NC-SA 4.0
// ============================================================

const PAISES = [
  {
    id: 'ar', nombre: 'Argentina', bandera: '🇦🇷', moneda: 'ARS', simbolo: '$',
    provincias: ['Buenos Aires','Ciudad de Buenos Aires','Catamarca','Chaco','Chubut',
      'Córdoba','Corrientes','Entre Ríos','Formosa','Jujuy','La Pampa','La Rioja',
      'Mendoza','Misiones','Neuquén','Río Negro','Salta','San Juan','San Luis',
      'Santa Cruz','Santa Fe','Santiago del Estero','Tierra del Fuego','Tucumán']
  },
  {
    id: 'es', nombre: 'España', bandera: '🇪🇸', moneda: 'EUR', simbolo: '€',
    provincias: ['Madrid','Barcelona','Valencia','Sevilla','Zaragoza','Málaga',
      'Murcia','Palma','Las Palmas','Bilbao','Alicante','Córdoba','Valladolid',
      'Vigo','Gijón','Granada','Elche','Oviedo','Badalona','Tarrasa']
  },
  {
    id: 'cl', nombre: 'Chile', bandera: '🇨🇱', moneda: 'CLP', simbolo: '$',
    provincias: ['Región Metropolitana','Valparaíso','Biobío','La Araucanía',
      'Los Lagos','Maule','O\'Higgins','Antofagasta','Coquimbo','Atacama',
      'Los Ríos','Magallanes','Arica y Parinacota','Tarapacá','Ñuble']
  },
  {
    id: 'uy', nombre: 'Uruguay', bandera: '🇺🇾', moneda: 'UYU', simbolo: '$',
    provincias: ['Montevideo','Canelones','Maldonado','Salto','Colonia','Paysandú',
      'Rivera','San José','Durazno','Florida','Soriano','Río Negro','Artigas',
      'Cerro Largo','Flores','Lavalleja','Rocha','Tacuarembó','Treinta y Tres']
  },
  {
    id: 'py', nombre: 'Paraguay', bandera: '🇵🇾', moneda: 'PYG', simbolo: '₲',
    provincias: ['Asunción','Central','Alto Paraná','Itapúa','Caaguazú','San Pedro',
      'Cordillera','Guairá','Paraguarí','Misiones','Ñeembucú','Amambay',
      'Canindeyú','Concepción','Presidente Hayes','Alto Paraguay','Boquerón']
  },
  {
    id: 'bo', nombre: 'Bolivia', bandera: '🇧🇴', moneda: 'BOB', simbolo: 'Bs',
    provincias: ['La Paz','Cochabamba','Santa Cruz','Oruro','Potosí',
      'Chuquisaca','Tarija','Beni','Pando']
  },
  {
    id: 'pe', nombre: 'Perú', bandera: '🇵🇪', moneda: 'PEN', simbolo: 'S/',
    provincias: ['Lima','Arequipa','La Libertad','Piura','Cajamarca','Cusco',
      'Junín','Lambayeque','Áncash','Loreto','Puno','Ica','San Martín',
      'Ucayali','Huánuco','Ayacucho','Apurímac','Tacna','Amazonas','Moquegua',
      'Tumbes','Pasco','Huancavelica','Madre de Dios']
  },
  {
    id: 'mx', nombre: 'México', bandera: '🇲🇽', moneda: 'MXN', simbolo: '$',
    provincias: ['Ciudad de México','Jalisco','Nuevo León','Veracruz','Puebla',
      'Guanajuato','Chiapas','Michoacán','Estado de México','Oaxaca','Chihuahua',
      'Guerrero','Tamaulipas','Baja California','Sonora','Coahuila','Hidalgo',
      'San Luis Potosí','Sinaloa','Tabasco','Yucatán','Querétaro','Morelos',
      'Durango','Zacatecas','Aguascalientes','Tlaxcala','Nayarit','Colima',
      'Campeche','Baja California Sur','Quintana Roo']
  }
];

const CADENAS = {
  ar: [
    { id: 'carrefour_ar', nombre: 'Carrefour', tipo: 'super', color: '#003087', iniciales: 'CF',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/200px-Carrefour_logo.svg.png' },
    { id: 'coto_ar', nombre: 'Coto', tipo: 'super', color: '#E30613', iniciales: 'CO', logo: null },
    { id: 'disco_ar', nombre: 'Disco', tipo: 'super', color: '#00A651', iniciales: 'DI', logo: null },
    { id: 'dia_ar', nombre: 'Día', tipo: 'super', color: '#E30613', iniciales: 'DÍA',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Dia_logo.svg/200px-Dia_logo.svg.png' },
    { id: 'jumbo_ar', nombre: 'Jumbo', tipo: 'super', color: '#009639', iniciales: 'JU', logo: null },
    { id: 'walmart_ar', nombre: 'Walmart', tipo: 'super', color: '#0071CE', iniciales: 'WM',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Walmart_Spark.svg/200px-Walmart_Spark.svg.png' },
    { id: 'vea_ar', nombre: 'Vea', tipo: 'super', color: '#EE3124', iniciales: 'VEA', logo: null },
    { id: 'chango_ar', nombre: 'ChangoMás', tipo: 'super', color: '#FECC00', iniciales: 'CM', logo: null },
    { id: 'toledo_ar', nombre: 'Toledo', tipo: 'super', color: '#0056A2', iniciales: 'TO', logo: null },
    { id: 'kiosko_ar', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  es: [
    { id: 'mercadona_es', nombre: 'Mercadona', tipo: 'super', color: '#FF6900', iniciales: 'ME', logo: null },
    { id: 'carrefour_es', nombre: 'Carrefour', tipo: 'super', color: '#003087', iniciales: 'CF',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Carrefour_logo.svg/200px-Carrefour_logo.svg.png' },
    { id: 'lidl_es', nombre: 'Lidl', tipo: 'super', color: '#0050AA', iniciales: 'LI', logo: null },
    { id: 'alcampo_es', nombre: 'Alcampo', tipo: 'super', color: '#E3002B', iniciales: 'AL', logo: null },
    { id: 'dia_es', nombre: 'Día', tipo: 'super', color: '#E30613', iniciales: 'DÍA',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Dia_logo.svg/200px-Dia_logo.svg.png' },
    { id: 'eroski_es', nombre: 'Eroski', tipo: 'super', color: '#E30613', iniciales: 'ER', logo: null },
    { id: 'kiosko_es', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  cl: [
    { id: 'jumbo_cl', nombre: 'Jumbo', tipo: 'super', color: '#009639', iniciales: 'JU', logo: null },
    { id: 'lider_cl', nombre: 'Lider', tipo: 'super', color: '#0071CE', iniciales: 'LI', logo: null },
    { id: 'santa_isabel_cl', nombre: 'Santa Isabel', tipo: 'super', color: '#E30613', iniciales: 'SI', logo: null },
    { id: 'unimarc_cl', nombre: 'Unimarc', tipo: 'super', color: '#FF6900', iniciales: 'UN', logo: null },
    { id: 'acuenta_cl', nombre: 'Acuenta', tipo: 'super', color: '#003087', iniciales: 'AC', logo: null },
    { id: 'kiosko_cl', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  uy: [
    { id: 'disco_uy', nombre: 'Disco', tipo: 'super', color: '#00A651', iniciales: 'DI', logo: null },
    { id: 'devoto_uy', nombre: 'Devoto', tipo: 'super', color: '#003087', iniciales: 'DV', logo: null },
    { id: 'geant_uy', nombre: 'Géant', tipo: 'super', color: '#E30613', iniciales: 'GE', logo: null },
    { id: 'tienda_inglesa_uy', nombre: 'Tienda Inglesa', tipo: 'super', color: '#006400', iniciales: 'TI', logo: null },
    { id: 'kiosko_uy', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  py: [
    { id: 'stock_py', nombre: 'Stock', tipo: 'super', color: '#E30613', iniciales: 'ST', logo: null },
    { id: 'superseis_py', nombre: 'Superseis', tipo: 'super', color: '#FF6900', iniciales: 'S6', logo: null },
    { id: 'big_py', nombre: 'Big', tipo: 'super', color: '#0056A2', iniciales: 'BIG', logo: null },
    { id: 'kiosko_py', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  bo: [
    { id: 'fidalga_bo', nombre: 'Fidalga', tipo: 'super', color: '#003087', iniciales: 'FI', logo: null },
    { id: 'hipermaxi_bo', nombre: 'Hipermaxi', tipo: 'super', color: '#E30613', iniciales: 'HM', logo: null },
    { id: 'ketal_bo', nombre: 'Ketal', tipo: 'super', color: '#FF6900', iniciales: 'KT', logo: null },
    { id: 'kiosko_bo', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  pe: [
    { id: 'wong_pe', nombre: 'Wong', tipo: 'super', color: '#E30613', iniciales: 'WO', logo: null },
    { id: 'metro_pe', nombre: 'Metro', tipo: 'super', color: '#003087', iniciales: 'MT', logo: null },
    { id: 'plaza_vea_pe', nombre: 'Plaza Vea', tipo: 'super', color: '#E30613', iniciales: 'PV', logo: null },
    { id: 'tottus_pe', nombre: 'Tottus', tipo: 'super', color: '#CC0000', iniciales: 'TO', logo: null },
    { id: 'kiosko_pe', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ],
  mx: [
    { id: 'walmart_mx', nombre: 'Walmart', tipo: 'super', color: '#0071CE', iniciales: 'WM',
      logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Walmart_Spark.svg/200px-Walmart_Spark.svg.png' },
    { id: 'soriana_mx', nombre: 'Soriana', tipo: 'super', color: '#E30613', iniciales: 'SO', logo: null },
    { id: 'chedraui_mx', nombre: 'Chedraui', tipo: 'super', color: '#003087', iniciales: 'CH', logo: null },
    { id: 'costco_mx', nombre: 'Costco', tipo: 'super', color: '#E30613', iniciales: 'CO', logo: null },
    { id: 'oxxo_mx', nombre: 'Oxxo', tipo: 'kiosk', color: '#E30613', iniciales: 'OX', logo: null },
    { id: 'kiosko_mx', nombre: 'Kiosco', tipo: 'kiosk', color: '#C8A882', iniciales: 'KI', logo: null }
  ]
};

const CATEGORIAS = [
  { id: 'lacteos',    nombre: 'Lácteos',      emoji: '🥛' },
  { id: 'panaderia',  nombre: 'Panadería',    emoji: '🍞' },
  { id: 'aceites',    nombre: 'Aceites',      emoji: '🫙' },
  { id: 'secos',      nombre: 'Secos',        emoji: '🌾' },
  { id: 'bebidas',    nombre: 'Bebidas',      emoji: '🥤' },
  { id: 'infusiones', nombre: 'Infusiones',   emoji: '🧉' },
  { id: 'carnes',     nombre: 'Carnes',       emoji: '🥩' },
  { id: 'frutas',     nombre: 'Frutas y verduras', emoji: '🥦' },
  { id: 'limpieza',   nombre: 'Limpieza',     emoji: '🧹' },
  { id: 'higiene',    nombre: 'Higiene',      emoji: '🧴' },
  { id: 'snacks',     nombre: 'Snacks',       emoji: '🍫' },
  { id: 'congelados', nombre: 'Congelados',   emoji: '🧊' }
];

const PRODUCTOS_DEMO = [
  { id: 'leche_1l',      nombre: 'Leche entera 1L',         categoria: 'lacteos',    emoji: '🥛' },
  { id: 'pan_lactal',    nombre: 'Pan lactal x12',          categoria: 'panaderia',  emoji: '🍞' },
  { id: 'aceite_900ml',  nombre: 'Aceite girasol 900ml',    categoria: 'aceites',    emoji: '🫙' },
  { id: 'arroz_1kg',     nombre: 'Arroz largo 1kg',         categoria: 'secos',      emoji: '🍚' },
  { id: 'azucar_1kg',    nombre: 'Azúcar 1kg',              categoria: 'secos',      emoji: '🧂' },
  { id: 'coca_2l',       nombre: 'Coca-Cola 2L',            categoria: 'bebidas',    emoji: '🥤' },
  { id: 'yerba_500g',    nombre: 'Yerba mate 500g',         categoria: 'infusiones', emoji: '🧉' },
  { id: 'harina_1kg',    nombre: 'Harina 0000 1kg',         categoria: 'secos',      emoji: '🌾' },
  { id: 'fideos_500g',   nombre: 'Fideos tallarín 500g',    categoria: 'secos',      emoji: '🍝' },
  { id: 'tomate_lata',   nombre: 'Tomate triturado 400g',   categoria: 'secos',      emoji: '🍅' },
  { id: 'manteca_200g',  nombre: 'Manteca 200g',            categoria: 'lacteos',    emoji: '🧈' },
  { id: 'huevos_12',     nombre: 'Huevos x12',              categoria: 'lacteos',    emoji: '🥚' }
];

// Generar precios de demo para visualización sin Supabase
function generarPreciosDemo(paisId, productoId) {
  const cadenas = (CADENAS[paisId] || CADENAS.ar).filter(c => c.tipo === 'super');
  const pais    = PAISES.find(p => p.id === paisId) || PAISES[0];
  const bases   = { ar: 850, es: 1.4, cl: 1100, uy: 55, py: 5500, bo: 8, pe: 4.5, mx: 28 };
  const base    = bases[paisId] || 850;
  const lats    = { ar: -34.6, es: 40.4, cl: -33.4, uy: -34.9, py: -25.3, bo: -16.5, pe: -12.0, mx: 19.4 };
  const lngs    = { ar: -58.4, es: -3.7, cl: -70.6, uy: -56.1, py: -57.6, bo: -68.1, pe: -77.0, mx: -99.1 };

  return cadenas.map((cadena, i) => {
    const factor = 0.82 + Math.random() * 0.55;
    const precio = parseFloat((base * factor).toFixed(2));
    const hace   = Math.floor(Math.random() * 72) + 1;
    const unit   = hace === 1 ? 'hora' : 'horas';
    return {
      cadena, precio,
      simbolo:   pais.simbolo,
      hace:      `hace ${hace} ${unit}`,
      reportes:  Math.floor(Math.random() * 25) + 2,
      lat:       lats[paisId] + (Math.random() - 0.5) * 0.18,
      lng:       lngs[paisId] + (Math.random() - 0.5) * 0.18,
      horario:   i % 3 === 0 ? '8:00 – 23:00' : i % 3 === 1 ? '7:00 – 22:00' : '9:00 – 21:00',
      direccion: `Av. Ejemplo ${100 + i * 150}, ${pais.nombre}`
    };
  }).sort((a, b) => a.precio - b.precio);
}

// Generar historial de 30 días
function generarHistorial(precioBase, simbolo) {
  const labels = [], datasets = {};
  const hoy    = new Date();
  const stores = ['Carrefour', 'Coto', 'Disco'];
  stores.forEach(s => { datasets[s] = []; });

  for (let i = 29; i >= 0; i--) {
    const d = new Date(hoy);
    d.setDate(d.getDate() - i);
    labels.push(`${d.getDate()}/${d.getMonth() + 1}`);
    stores.forEach((s, idx) => {
      const offset = idx * 0.08;
      const var2   = precioBase * (0.88 + offset + Math.random() * 0.28);
      datasets[s].push(parseFloat(var2.toFixed(2)));
    });
  }
  return { labels, datasets, simbolo };
}

// Obtener país por ID
function getPais(id) { return PAISES.find(p => p.id === id) || PAISES[0]; }

// Obtener cadenas de un país
function getCadenas(paisId) { return CADENAS[paisId] || []; }

// Formatear precio
function formatPrecio(precio, simbolo) {
  if (precio >= 1000) return `${simbolo}${precio.toLocaleString('es-AR')}`;
  return `${simbolo}${precio.toFixed(2)}`;
}

// ✓ data.js — completo
