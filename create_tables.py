import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Todas las tablas necesarias
sql_commands = [
    # Al inicio de create_tables.py, antes de los CREATE TABLE
    "ALTER TABLE categorias ADD COLUMN IF NOT EXISTS codigo_categoria VARCHAR(10);",
    
    # Tipos de cliente
    "CREATE TABLE IF NOT EXISTS tipos_cliente (id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, activo BOOLEAN DEFAULT true);",
    
    # Categorías
    "CREATE TABLE IF NOT EXISTS categorias (categoria_id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, codigo_categoria VARCHAR(10) NOT NULL, activa BOOLEAN DEFAULT true, orden_visualizacion INTEGER DEFAULT 0, fecha_creacion TIMESTAMP DEFAULT now());",
    
    # Productos
    "CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, codigo_producto VARCHAR(20) NOT NULL, codigo_barras VARCHAR(50), nombre VARCHAR(200) NOT NULL, descripcion TEXT, categoria_id INTEGER REFERENCES categorias(categoria_id), unidad_medida VARCHAR(20) NOT NULL DEFAULT 'unidad', precio_unitario NUMERIC(10,2) NOT NULL, precio_mayorista NUMERIC(10,2), precio_distribuidor NUMERIC(10,2), stock_minimo INTEGER DEFAULT 0, stock_actual INTEGER DEFAULT 0, activo BOOLEAN DEFAULT true, destacado BOOLEAN DEFAULT false, fecha_creacion TIMESTAMP DEFAULT now(), fecha_modificacion TIMESTAMP DEFAULT now(), imagen_url VARCHAR(500), especificaciones JSONB DEFAULT '{}', metadatos JSONB DEFAULT '{}', peso_unitario DOUBLE PRECISION, volumen_unitario DOUBLE PRECISION);",
    
    # Precios
    "CREATE TABLE IF NOT EXISTS precios (id SERIAL PRIMARY KEY, producto_id INTEGER NOT NULL REFERENCES productos(id), tipo_cliente_id INTEGER NOT NULL REFERENCES tipos_cliente(id), precio NUMERIC(10,2) NOT NULL);",
    
    # Vendedores
    "CREATE TABLE IF NOT EXISTS vendedores (vendedor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_vendedor VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion TEXT, distrito VARCHAR(100), provincia VARCHAR(100), departamento VARCHAR(100), password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, latitud_actual DOUBLE PRECISION, longitud_actual DOUBLE PRECISION, precision_gps DOUBLE PRECISION, ultima_ubicacion TIMESTAMP, configuraciones JSONB DEFAULT '{}');",
    
    # Evaluadores
    "CREATE TABLE IF NOT EXISTS evaluadores (evaluador_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_evaluador VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion_trabajo TEXT, distrito_asignado VARCHAR(100), provincia_asignada VARCHAR(100), departamento_asignado VARCHAR(100), password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, latitud_actual DOUBLE PRECISION, longitud_actual DOUBLE PRECISION, precision_gps DOUBLE PRECISION, ultima_ubicacion TIMESTAMP, configuraciones JSONB DEFAULT '{}', areas_evaluacion JSONB DEFAULT '[]');",
    
    # Supervisores
    "CREATE TABLE IF NOT EXISTS supervisores (supervisor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_supervisor VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), cargo VARCHAR(100), nivel_acceso VARCHAR(20) DEFAULT 'supervisor', password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, permisos JSONB DEFAULT '{}', configuraciones JSONB DEFAULT '{}');",
    
    # Clientes
    "CREATE TABLE IF NOT EXISTS clientes (id SERIAL PRIMARY KEY, codigo_cliente VARCHAR(10) NOT NULL UNIQUE, nombre_comercial VARCHAR(200) NOT NULL, razon_social VARCHAR(250), ruc VARCHAR(11), telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion_completa TEXT NOT NULL, referencia VARCHAR(200), distrito VARCHAR(100) NOT NULL, provincia VARCHAR(100) NOT NULL, departamento VARCHAR(100) NOT NULL, codigo_postal VARCHAR(10), latitud DOUBLE PRECISION, longitud DOUBLE PRECISION, precision_gps DOUBLE PRECISION, activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), fecha_modificacion TIMESTAMP DEFAULT now(), configuraciones JSONB DEFAULT '{}', metadatos JSONB DEFAULT '{}', tipo_cliente_id INTEGER REFERENCES tipos_cliente(id));",
    
    # Pedidos
    "CREATE TABLE IF NOT EXISTS pedidos (id SERIAL PRIMARY KEY, codigo_pedido VARCHAR(20), cliente_id INTEGER NOT NULL REFERENCES clientes(id), vendedor_id INTEGER NOT NULL REFERENCES vendedores(vendedor_id), aprobador_id INTEGER, tipo_aprobador VARCHAR(20), fecha_creacion TIMESTAMP NOT NULL DEFAULT now(), fecha_decision TIMESTAMP, monto_total NUMERIC(10,2) NOT NULL, metodo_pago VARCHAR(15) NOT NULL, estado VARCHAR(20) NOT NULL DEFAULT 'pendiente_aprobacion', observaciones TEXT, latitud DOUBLE PRECISION, longitud DOUBLE PRECISION);",
    
    # Pedido Items
    "CREATE TABLE IF NOT EXISTS pedido_items (id SERIAL PRIMARY KEY, pedido_id INTEGER NOT NULL REFERENCES pedidos(id), producto_id INTEGER NOT NULL REFERENCES productos(id), unidad_medida_venta VARCHAR(50) NOT NULL, cantidad NUMERIC(10,2) NOT NULL, precio_unitario_venta NUMERIC(10,2) NOT NULL, subtotal NUMERIC(10,2) NOT NULL);",
    
    # Sesiones Activas
    "CREATE TABLE IF NOT EXISTS sesiones_activas (sesion_id VARCHAR(50) PRIMARY KEY, vendedor_id INTEGER REFERENCES vendedores(vendedor_id), evaluador_id INTEGER REFERENCES evaluadores(evaluador_id), supervisor_id INTEGER REFERENCES supervisores(supervisor_id), tipo_usuario VARCHAR(20) NOT NULL, token_acceso VARCHAR(500) NOT NULL, ip_origen VARCHAR(45), user_agent TEXT, fecha_inicio TIMESTAMP DEFAULT now(), fecha_expiracion TIMESTAMP NOT NULL, ultima_actividad TIMESTAMP DEFAULT now(), activa BOOLEAN DEFAULT true, dispositivo_info JSONB DEFAULT '{}');"
]

with engine.begin() as conn:
    for sql in sql_commands:
        try:
            conn.execute(text(sql))
            print(f"Tabla creada/verificada")
        except Exception as e:
            print(f"Error creando tabla: {e}")
        
print("Todas las tablas procesadas")

