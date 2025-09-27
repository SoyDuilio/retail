-- SCRIPT 3: CREAR TABLAS DE CLIENTES Y PRODUCTOS

-- Tabla Clientes
CREATE TABLE clientes (
    cliente_id SERIAL PRIMARY KEY,
    codigo_cliente VARCHAR(10) UNIQUE NOT NULL,
    nombre_comercial VARCHAR(200) NOT NULL,
    razon_social VARCHAR(250),
    ruc VARCHAR(11) UNIQUE,
    tipo_cliente VARCHAR(50) NOT NULL DEFAULT 'bodega',
    telefono VARCHAR(15) NOT NULL,
    email VARCHAR(150),
    direccion_completa TEXT NOT NULL,
    referencia VARCHAR(200),
    distrito VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    codigo_postal VARCHAR(10),
    latitud FLOAT,
    longitud FLOAT,
    precision_gps FLOAT,
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    fecha_modificacion TIMESTAMP DEFAULT NOW(),
    configuraciones JSONB DEFAULT '{}',
    metadatos JSONB DEFAULT '{}'
);

-- Tabla Categorías de Productos  
CREATE TABLE categorias (
    categoria_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    codigo_categoria VARCHAR(10) UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    orden_visualizacion INTEGER DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Tabla Productos
CREATE TABLE productos (
    producto_id SERIAL PRIMARY KEY,
    codigo_producto VARCHAR(20) UNIQUE NOT NULL,
    codigo_barras VARCHAR(50) UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER REFERENCES categorias(categoria_id),
    unidad_medida VARCHAR(20) NOT NULL DEFAULT 'unidad',
    peso_unitario FLOAT,
    volumen_unitario FLOAT,
    precio_unitario DECIMAL(10,2) NOT NULL,
    precio_mayorista DECIMAL(10,2),
    precio_distribuidor DECIMAL(10,2),
    stock_minimo INTEGER DEFAULT 0,
    stock_actual INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    destacado BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    fecha_modificacion TIMESTAMP DEFAULT NOW(),
    imagen_url VARCHAR(500),
    especificaciones JSONB DEFAULT '{}',
    metadatos JSONB DEFAULT '{}'
);