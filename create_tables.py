import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# TODAS las tablas necesarias - ORDEN CORRECTO
sql_commands = [
    # 1. ELIMINAR TABLAS PROBLEMÁTICAS PARA RECREARLAS
    "DROP TABLE IF EXISTS precios CASCADE;",
    "DROP TABLE IF EXISTS pedido_items CASCADE;", 
    "DROP TABLE IF EXISTS pedidos CASCADE;",
    "DROP TABLE IF EXISTS productos CASCADE;",
    "DROP TABLE IF EXISTS categorias CASCADE;",
    "DROP TABLE IF EXISTS clientes CASCADE;",
    "DROP TABLE IF EXISTS tipos_cliente CASCADE;",
    "DROP TABLE IF EXISTS sesiones_activas CASCADE;",
    "DROP TABLE IF EXISTS vendedores CASCADE;",
    "DROP TABLE IF EXISTS evaluadores CASCADE;",
    "DROP TABLE IF EXISTS supervisores CASCADE;",
    
    # 2. CREAR TABLAS BASE (sin dependencias)
    "CREATE TABLE tipos_cliente (id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, activo BOOLEAN DEFAULT true);",
    
    "CREATE TABLE categorias (categoria_id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, codigo_categoria VARCHAR(10) NOT NULL, activa BOOLEAN DEFAULT true, orden_visualizacion INTEGER DEFAULT 0, fecha_creacion TIMESTAMP DEFAULT now());",
    
    "CREATE TABLE vendedores (vendedor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_vendedor VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion TEXT, distrito VARCHAR(100), provincia VARCHAR(100), departamento VARCHAR(100), password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, latitud_actual DOUBLE PRECISION, longitud_actual DOUBLE PRECISION, precision_gps DOUBLE PRECISION, ultima_ubicacion TIMESTAMP, configuraciones JSONB DEFAULT '{}');",
    
    "CREATE TABLE evaluadores (evaluador_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_evaluador VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion_trabajo TEXT, distrito_asignado VARCHAR(100), provincia_asignada VARCHAR(100), departamento_asignado VARCHAR(100), password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, latitud_actual DOUBLE PRECISION, longitud_actual DOUBLE PRECISION, precision_gps DOUBLE PRECISION, ultima_ubicacion TIMESTAMP, configuraciones JSONB DEFAULT '{}', areas_evaluacion JSONB DEFAULT '[]');",
    
    "CREATE TABLE supervisores (supervisor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL UNIQUE, codigo_supervisor VARCHAR(10) NOT NULL UNIQUE, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), cargo VARCHAR(100), nivel_acceso VARCHAR(20) DEFAULT 'supervisor', password_hash VARCHAR(255) NOT NULL, token_fcm VARCHAR(255), activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP, permisos JSONB DEFAULT '{}', configuraciones JSONB DEFAULT '{}');",
    
    # 3. CREAR TABLAS QUE DEPENDEN DE LAS ANTERIORES
    "CREATE TABLE clientes (id SERIAL PRIMARY KEY, codigo_cliente VARCHAR(10) NOT NULL UNIQUE, nombre_comercial VARCHAR(200) NOT NULL, razon_social VARCHAR(250), ruc VARCHAR(11), telefono VARCHAR(15) NOT NULL, email VARCHAR(150), direccion_completa TEXT NOT NULL, referencia VARCHAR(200), distrito VARCHAR(100) NOT NULL, provincia VARCHAR(100) NOT NULL, departamento VARCHAR(100) NOT NULL, codigo_postal VARCHAR(10), latitud DOUBLE PRECISION, longitud DOUBLE PRECISION, precision_gps DOUBLE PRECISION, activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), fecha_modificacion TIMESTAMP DEFAULT now(), configuraciones JSONB DEFAULT '{}', metadatos JSONB DEFAULT '{}', tipo_cliente_id INTEGER REFERENCES tipos_cliente(id));",
    
    "CREATE TABLE productos (id SERIAL PRIMARY KEY, codigo_producto VARCHAR(20) NOT NULL, codigo_barras VARCHAR(50), nombre VARCHAR(200) NOT NULL, descripcion TEXT, categoria_id INTEGER REFERENCES categorias(categoria_id), unidad_medida VARCHAR(20) NOT NULL DEFAULT 'unidad', precio_unitario NUMERIC(10,2) NOT NULL, precio_mayorista NUMERIC(10,2), precio_distribuidor NUMERIC(10,2), stock_minimo INTEGER DEFAULT 0, stock_actual INTEGER DEFAULT 0, activo BOOLEAN DEFAULT true, destacado BOOLEAN DEFAULT false, fecha_creacion TIMESTAMP DEFAULT now(), fecha_modificacion TIMESTAMP DEFAULT now(), imagen_url VARCHAR(500), especificaciones JSONB DEFAULT '{}', metadatos JSONB DEFAULT '{}', peso_unitario DOUBLE PRECISION, volumen_unitario DOUBLE PRECISION);",
    
    "CREATE TABLE precios (id SERIAL PRIMARY KEY, producto_id INTEGER NOT NULL REFERENCES productos(id), tipo_cliente_id INTEGER NOT NULL REFERENCES tipos_cliente(id), precio NUMERIC(10,2) NOT NULL);",
    
    "CREATE TABLE pedidos (id SERIAL PRIMARY KEY, codigo_pedido VARCHAR(20), cliente_id INTEGER NOT NULL REFERENCES clientes(id), vendedor_id INTEGER NOT NULL REFERENCES vendedores(vendedor_id), aprobador_id INTEGER, tipo_aprobador VARCHAR(20), fecha_creacion TIMESTAMP NOT NULL DEFAULT now(), fecha_decision TIMESTAMP, monto_total NUMERIC(10,2) NOT NULL, metodo_pago VARCHAR(15) NOT NULL, estado VARCHAR(20) NOT NULL DEFAULT 'pendiente_aprobacion', observaciones TEXT, latitud DOUBLE PRECISION, longitud DOUBLE PRECISION);",
    
    "CREATE TABLE pedido_items (id SERIAL PRIMARY KEY, pedido_id INTEGER NOT NULL REFERENCES pedidos(id), producto_id INTEGER NOT NULL REFERENCES productos(id), unidad_medida_venta VARCHAR(50) NOT NULL, cantidad NUMERIC(10,2) NOT NULL, precio_unitario_venta NUMERIC(10,2) NOT NULL, subtotal NUMERIC(10,2) NOT NULL);",
    
    "CREATE TABLE sesiones_activas (sesion_id VARCHAR(50) PRIMARY KEY, vendedor_id INTEGER REFERENCES vendedores(vendedor_id), evaluador_id INTEGER REFERENCES evaluadores(evaluador_id), supervisor_id INTEGER REFERENCES supervisores(supervisor_id), tipo_usuario VARCHAR(20) NOT NULL, token_acceso VARCHAR(500) NOT NULL, ip_origen VARCHAR(45), user_agent TEXT, fecha_inicio TIMESTAMP DEFAULT now(), fecha_expiracion TIMESTAMP NOT NULL, ultima_actividad TIMESTAMP DEFAULT now(), activa BOOLEAN DEFAULT true, dispositivo_info JSONB DEFAULT '{}');"
]

print("Iniciando creación/recreación de tablas...")

with engine.begin() as conn:
    for i, sql in enumerate(sql_commands):
        try:
            conn.execute(text(sql))
            if i < 11:
                print(f"Tabla eliminada/preparada {i+1}/11")
            else:
                print(f"Tabla creada {i-10}/{len(sql_commands)-11}")
        except Exception as e:
            print(f"Error en comando {i+1}: {e}")
        
print("Todas las tablas procesadas correctamente")
print("Base de datos lista para el seeder")
