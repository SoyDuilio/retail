import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Solo crear las tablas que necesitas
sql_commands = [
    "CREATE TABLE IF NOT EXISTS categorias (categoria_id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, codigo_categoria VARCHAR(10) NOT NULL, activa BOOLEAN DEFAULT true, orden_visualizacion INTEGER DEFAULT 0, fecha_creacion TIMESTAMP DEFAULT now());",
    "CREATE TABLE IF NOT EXISTS tipos_cliente (id SERIAL PRIMARY KEY, nombre VARCHAR(100) NOT NULL, descripcion TEXT, activo BOOLEAN DEFAULT true);",
    "CREATE TABLE IF NOT EXISTS productos (id SERIAL PRIMARY KEY, codigo_producto VARCHAR(20) NOT NULL, codigo_barras VARCHAR(50), nombre VARCHAR(200) NOT NULL, descripcion TEXT, categoria_id INTEGER REFERENCES categorias(categoria_id), unidad_medida VARCHAR(20) NOT NULL DEFAULT 'unidad', precio_unitario NUMERIC(10,2) NOT NULL, stock_minimo INTEGER DEFAULT 0, stock_actual INTEGER DEFAULT 0, activo BOOLEAN DEFAULT true, destacado BOOLEAN DEFAULT false, fecha_creacion TIMESTAMP DEFAULT now(), fecha_modificacion TIMESTAMP DEFAULT now());",
    "CREATE TABLE IF NOT EXISTS precios (id SERIAL PRIMARY KEY, producto_id INTEGER NOT NULL REFERENCES productos(id), tipo_cliente_id INTEGER NOT NULL REFERENCES tipos_cliente(id), precio NUMERIC(10,2) NOT NULL);",
    "CREATE TABLE IF NOT EXISTS vendedores (vendedor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL, codigo_vendedor VARCHAR(10) NOT NULL, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), password_hash VARCHAR(255) NOT NULL, activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP);",
    "CREATE TABLE IF NOT EXISTS evaluadores (evaluador_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL, codigo_evaluador VARCHAR(10) NOT NULL, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), password_hash VARCHAR(255) NOT NULL, activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP);",
    "CREATE TABLE IF NOT EXISTS supervisores (supervisor_id SERIAL PRIMARY KEY, dni VARCHAR(8) NOT NULL, codigo_supervisor VARCHAR(10) NOT NULL, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(150) NOT NULL, telefono VARCHAR(15) NOT NULL, email VARCHAR(150), password_hash VARCHAR(255) NOT NULL, activo BOOLEAN DEFAULT true, verificado BOOLEAN DEFAULT false, fecha_registro TIMESTAMP DEFAULT now(), ultima_conexion TIMESTAMP);",
    "CREATE TABLE IF NOT EXISTS clientes (id SERIAL PRIMARY KEY, codigo_cliente VARCHAR(10) NOT NULL, nombre_comercial VARCHAR(200) NOT NULL, razon_social VARCHAR(250), ruc VARCHAR(11), telefono VARCHAR(15) NOT NULL, direccion_completa TEXT NOT NULL, distrito VARCHAR(100) NOT NULL, provincia VARCHAR(100) NOT NULL, departamento VARCHAR(100) NOT NULL, activo BOOLEAN DEFAULT true, tipo_cliente_id INTEGER REFERENCES tipos_cliente(id), fecha_registro TIMESTAMP DEFAULT now());"
]

with engine.begin() as conn:
    for sql in sql_commands:
        conn.execute(text(sql))
        
print("Tablas creadas exitosamente")