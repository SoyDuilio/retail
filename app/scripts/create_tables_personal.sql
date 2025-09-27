-- SCRIPT 1: CREAR TABLAS BÁSICAS
-- Copia y pega esto en PGAdmin línea por línea:

-- Tabla Vendedores
CREATE TABLE vendedores (
    vendedor_id SERIAL PRIMARY KEY,
    dni VARCHAR(8) UNIQUE NOT NULL,
    codigo_vendedor VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    email VARCHAR(150) UNIQUE,
    direccion TEXT,
    distrito VARCHAR(100),
    provincia VARCHAR(100),
    departamento VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    token_fcm VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    ultima_conexion TIMESTAMP,
    latitud_actual FLOAT,
    longitud_actual FLOAT,
    precision_gps FLOAT,
    ultima_ubicacion TIMESTAMP,
    configuraciones JSONB DEFAULT '{}'
);

-- Tabla Evaluadores
CREATE TABLE evaluadores (
    evaluador_id SERIAL PRIMARY KEY,
    dni VARCHAR(8) UNIQUE NOT NULL,
    codigo_evaluador VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    email VARCHAR(150) UNIQUE,
    direccion_trabajo TEXT,
    distrito_asignado VARCHAR(100),
    provincia_asignada VARCHAR(100),
    departamento_asignado VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    token_fcm VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    ultima_conexion TIMESTAMP,
    latitud_actual FLOAT,
    longitud_actual FLOAT,
    precision_gps FLOAT,
    ultima_ubicacion TIMESTAMP,
    configuraciones JSONB DEFAULT '{}',
    areas_evaluacion JSONB DEFAULT '[]'
);

-- Tabla Supervisores
CREATE TABLE supervisores (
    supervisor_id SERIAL PRIMARY KEY,
    dni VARCHAR(8) UNIQUE NOT NULL,
    codigo_supervisor VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    telefono VARCHAR(15) NOT NULL,
    email VARCHAR(150) UNIQUE,
    cargo VARCHAR(100),
    nivel_acceso VARCHAR(20) DEFAULT 'supervisor',
    password_hash VARCHAR(255) NOT NULL,
    token_fcm VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    verificado BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    ultima_conexion TIMESTAMP,
    permisos JSONB DEFAULT '{}',
    configuraciones JSONB DEFAULT '{}'
);

-- Tabla Sesiones Activas
CREATE TABLE sesiones_activas (
    sesion_id VARCHAR(50) PRIMARY KEY,
    vendedor_id INTEGER REFERENCES vendedores(vendedor_id),
    evaluador_id INTEGER REFERENCES evaluadores(evaluador_id),
    supervisor_id INTEGER REFERENCES supervisores(supervisor_id),
    tipo_usuario VARCHAR(20) NOT NULL,
    token_acceso VARCHAR(500) NOT NULL,
    ip_origen VARCHAR(45),
    user_agent TEXT,
    fecha_inicio TIMESTAMP DEFAULT NOW(),
    fecha_expiracion TIMESTAMP NOT NULL,
    ultima_actividad TIMESTAMP DEFAULT NOW(),
    activa BOOLEAN DEFAULT TRUE,
    dispositivo_info JSONB DEFAULT '{}'
);