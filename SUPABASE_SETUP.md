# Supabase Setup — PrecioVista

Seguí estos pasos exactos para configurar la base de datos.

---

## 1. Crear el proyecto

1. Entrá a [supabase.com](https://supabase.com) y creá una cuenta gratuita
2. Clic en **New Project**
3. Elegí un nombre (ej: `preciovista`) y una contraseña de base de datos segura
4. Región: elegí la más cercana a tu país
5. Esperá ~2 minutos a que se cree

---

## 2. Ejecutar el schema SQL

Andá a **SQL Editor** en el panel de Supabase y pegá y ejecutá este SQL completo:

```sql
-- Tabla de usuarios (extiende auth.users de Supabase)
CREATE TABLE IF NOT EXISTS usuarios (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email       TEXT NOT NULL,
  nombre      TEXT NOT NULL,
  avatar_url  TEXT,
  rol         TEXT NOT NULL DEFAULT 'user' CHECK (rol IN ('user','admin')),
  baneado     BOOLEAN NOT NULL DEFAULT FALSE,
  motivo_ban  TEXT,
  reportes_count INTEGER NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de comercios
CREATE TABLE IF NOT EXISTS comercios (
  id          TEXT PRIMARY KEY,
  nombre      TEXT NOT NULL,
  tipo        TEXT NOT NULL CHECK (tipo IN ('super','kiosk','pharmacy')),
  pais_id     TEXT NOT NULL,
  provincia   TEXT,
  direccion   TEXT,
  lat         DOUBLE PRECISION,
  lng         DOUBLE PRECISION,
  horario     TEXT,
  logo_url    TEXT,
  color       TEXT DEFAULT '#2563EB',
  iniciales   TEXT,
  estrellas_promedio DOUBLE PRECISION DEFAULT 0,
  resenas_count INTEGER DEFAULT 0,
  creado_por  UUID REFERENCES auth.users(id),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
  id          TEXT PRIMARY KEY,
  nombre      TEXT NOT NULL,
  categoria   TEXT,
  emoji       TEXT DEFAULT '🛒',
  codigo_barras TEXT,
  imagen_url  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de precios (núcleo del sistema)
CREATE TABLE IF NOT EXISTS precios (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  producto_id TEXT NOT NULL REFERENCES productos(id),
  comercio_id TEXT NOT NULL REFERENCES comercios(id),
  usuario_id  UUID NOT NULL REFERENCES auth.users(id),
  precio      NUMERIC(12,2) NOT NULL CHECK (precio > 0),
  moneda      TEXT NOT NULL DEFAULT 'ARS',
  verificado  BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de reseñas
CREATE TABLE IF NOT EXISTS resenas (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comercio_id TEXT NOT NULL REFERENCES comercios(id),
  usuario_id  UUID NOT NULL REFERENCES auth.users(id),
  estrellas   INTEGER NOT NULL CHECK (estrellas BETWEEN 1 AND 5),
  comentario  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(comercio_id, usuario_id)
);

-- Función para incrementar reportes
CREATE OR REPLACE FUNCTION incrementar_reportes(uid UUID)
RETURNS void AS $$
  UPDATE usuarios SET reportes_count = reportes_count + 1 WHERE id = uid;
$$ LANGUAGE sql SECURITY DEFINER;

-- Función para actualizar estrellas promedio
CREATE OR REPLACE FUNCTION actualizar_estrellas()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE comercios SET
    estrellas_promedio = (SELECT AVG(estrellas) FROM resenas WHERE comercio_id = NEW.comercio_id),
    resenas_count      = (SELECT COUNT(*)        FROM resenas WHERE comercio_id = NEW.comercio_id)
  WHERE id = NEW.comercio_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_actualizar_estrellas
AFTER INSERT OR UPDATE ON resenas
FOR EACH ROW EXECUTE FUNCTION actualizar_estrellas();

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_precios_producto  ON precios(producto_id);
CREATE INDEX IF NOT EXISTS idx_precios_comercio  ON precios(comercio_id);
CREATE INDEX IF NOT EXISTS idx_precios_fecha     ON precios(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comercios_pais    ON comercios(pais_id);
CREATE INDEX IF NOT EXISTS idx_productos_nombre  ON productos USING gin(to_tsvector('spanish', nombre));
```

---

## 3. Configurar Row Level Security (RLS)

Pegá y ejecutá este SQL para proteger los datos:

```sql
-- Habilitar RLS en todas las tablas
ALTER TABLE usuarios   ENABLE ROW LEVEL SECURITY;
ALTER TABLE comercios  ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos  ENABLE ROW LEVEL SECURITY;
ALTER TABLE precios    ENABLE ROW LEVEL SECURITY;
ALTER TABLE resenas    ENABLE ROW LEVEL SECURITY;

-- USUARIOS: cada uno ve solo su fila, admins ven todo
CREATE POLICY "usuarios_select" ON usuarios FOR SELECT USING (auth.uid() = id OR EXISTS (SELECT 1 FROM usuarios WHERE id = auth.uid() AND rol = 'admin'));
CREATE POLICY "usuarios_insert" ON usuarios FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "usuarios_update" ON usuarios FOR UPDATE USING (auth.uid() = id OR EXISTS (SELECT 1 FROM usuarios WHERE id = auth.uid() AND rol = 'admin'));

-- COMERCIOS: todos pueden ver, solo autenticados pueden insertar
CREATE POLICY "comercios_select" ON comercios FOR SELECT USING (true);
CREATE POLICY "comercios_insert" ON comercios FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- PRODUCTOS: todos pueden ver
CREATE POLICY "productos_select" ON productos FOR SELECT USING (true);
CREATE POLICY "productos_insert" ON productos FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- PRECIOS: todos ven precios verificados, usuarios autenticados pueden insertar los suyos
CREATE POLICY "precios_select" ON precios FOR SELECT USING (verificado = true OR usuario_id = auth.uid());
CREATE POLICY "precios_insert" ON precios FOR INSERT WITH CHECK (auth.uid() IS NOT NULL AND auth.uid() = usuario_id);

-- RESEÑAS: todos ven, autenticados pueden insertar/actualizar las suyas
CREATE POLICY "resenas_select" ON resenas FOR SELECT USING (true);
CREATE POLICY "resenas_insert" ON resenas FOR INSERT WITH CHECK (auth.uid() IS NOT NULL AND auth.uid() = usuario_id);
CREATE POLICY "resenas_update" ON resenas FOR UPDATE USING (auth.uid() = usuario_id);
```

---

## 4. Insertar datos iniciales (cadenas)

```sql
-- Cadenas de Argentina (ejemplo)
INSERT INTO comercios (id, nombre, tipo, pais_id, color, iniciales) VALUES
  ('carrefour_ar', 'Carrefour',  'super', 'ar', '#003087', 'CF'),
  ('coto_ar',      'Coto',       'super', 'ar', '#E30613', 'CO'),
  ('disco_ar',     'Disco',      'super', 'ar', '#00A651', 'DI'),
  ('dia_ar',       'Día',        'super', 'ar', '#E30613', 'DÍA'),
  ('jumbo_ar',     'Jumbo',      'super', 'ar', '#009639', 'JU'),
  ('walmart_ar',   'Walmart',    'super', 'ar', '#0071CE', 'WM'),
  ('chango_ar',    'ChangoMás',  'super', 'ar', '#FECC00', 'CM'),
  ('kiosko_ar',    'Kiosco',     'kiosk', 'ar', '#C8A882', 'KI')
ON CONFLICT (id) DO NOTHING;

-- Productos base
INSERT INTO productos (id, nombre, categoria, emoji) VALUES
  ('leche_1l',     'Leche entera 1L',       'lacteos',    '🥛'),
  ('pan_lactal',   'Pan lactal x12',         'panaderia',  '🍞'),
  ('aceite_900ml', 'Aceite girasol 900ml',   'aceites',    '🫙'),
  ('arroz_1kg',    'Arroz largo 1kg',        'secos',      '🍚'),
  ('azucar_1kg',   'Azúcar 1kg',             'secos',      '🧂'),
  ('coca_2l',      'Coca-Cola 2L',           'bebidas',    '🥤'),
  ('yerba_500g',   'Yerba mate 500g',        'infusiones', '🧉'),
  ('harina_1kg',   'Harina 0000 1kg',        'secos',      '🌾'),
  ('fideos_500g',  'Fideos tallarín 500g',   'secos',      '🍝'),
  ('huevos_12',    'Huevos x12',             'lacteos',    '🥚')
ON CONFLICT (id) DO NOTHING;
```

---

## 5. Configurar OAuth (Google y Microsoft)

### Google:
1. Andá a [console.cloud.google.com](https://console.cloud.google.com)
2. Creá un proyecto → **APIs & Services → Credentials → Create OAuth Client**
3. Tipo: Web application
4. Authorized redirect URI: `https://TU_PROYECTO.supabase.co/auth/v1/callback`
5. Copiá Client ID y Client Secret
6. En Supabase → **Authentication → Providers → Google** → pegá las credenciales

### Microsoft:
1. Andá a [portal.azure.com](https://portal.azure.com) → **App registrations → New**
2. Redirect URI: `https://TU_PROYECTO.supabase.co/auth/v1/callback`
3. En **Certificates & secrets → New client secret**
4. En Supabase → **Authentication → Providers → Azure** → pegá Application ID y Secret

---

## 6. Actualizar js/supabase.js

```javascript
const SUPABASE_URL  = 'https://TU_PROYECTO.supabase.co';  // Tu URL real
const SUPABASE_ANON = 'eyJ...';                            // Tu anon key real
const ADMIN_EMAIL   = 'tu@email.com';                      // Tu email real
```

---

## 7. Primer usuario admin

Después de registrarte en la app con tu email:

```sql
-- Ejecutá esto en el SQL Editor de Supabase con tu email real
UPDATE usuarios SET rol = 'admin' WHERE email = 'tu@email.com';
```

Listo. Ya podés acceder a `/pages/admin.html`.
