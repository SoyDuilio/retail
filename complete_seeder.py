# complete_seeder.py - Ejecutar en Railway y local
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import random
from decimal import Decimal
from dotenv import load_dotenv
import bcrypt

# Detectar entorno
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL requerida")

engine = create_engine(DATABASE_URL)

def hash_password(password):
    """Genera hash de contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verificar_y_crear_tipos_cliente():
    """Verifica y crea tipos de cliente si no existen"""
    tipos_base = [
        ("bodega", "Precio minorista para bodegas"),
        ("minimarket", "Precio para minimarkets y autoservicios"),
        ("restaurante", "Precio para restaurantes y hoteles"),
        ("mayorista", "Precio mayorista para distribuidores")
    ]
    
    print("🏷️ Creando tipos de cliente...")
    with engine.begin() as conn:
        for nombre, descripcion in tipos_base:  # ← FALTABA ESTA LÍNEA
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM tipos_cliente WHERE nombre = :nombre)
            """), {"nombre": nombre}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO tipos_cliente (nombre, descripcion)
                    VALUES (:nombre, :descripcion)
                """), {
                    "nombre": nombre,
                    "descripcion": descripcion
                })
                print(f"✅ Tipo cliente creado: {nombre}")

def verificar_y_crear_categorias():
    """Verifica y crea categorías si no existen"""
    categorias_base = [
        ("Bebidas", "BEB", "Bebidas gaseosas, jugos, agua"),
        ("Abarrotes", "ABR", "Productos de abarrotes y despensa"),
        ("Snacks", "SNK", "Galletas, papas fritas, dulces"),
        ("Lácteos", "LAC", "Leche, quesos, yogurt"),
        ("Carnes", "CAR", "Carnes y embutidos"),
        ("Frutas y Verduras", "FRU", "Productos frescos"),
        ("Panadería", "PAN", "Pan y productos de panadería"),
        ("Limpieza", "LIM", "Productos de limpieza y hogar")
    ]
    
    with engine.begin() as conn:
        for nombre, codigo, descripcion in categorias_base:
            # Verificar si existe
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM categorias WHERE codigo_categoria = :codigo)
            """), {"codigo": codigo}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO categorias (nombre, codigo_categoria, descripcion, activa)
                    VALUES (:nombre, :codigo, :descripcion, true)
                """), {
                    "nombre": nombre,
                    "codigo": codigo, 
                    "descripcion": descripcion
                })
                print(f"✅ Categoría creada: {nombre}")

def crear_usuarios_base():
    """Crea usuarios base para el sistema"""
    print("👥 Creando usuarios base...")
    
    # Vendedores
    vendedores = [
        ("12345678", "VEN001", "Juan", "Pérez García", "987654321", "juan.perez@distribuidora.com"),
        ("87654321", "VEN002", "María", "González López", "987654322", "maria.gonzalez@distribuidora.com"),
        ("11223344", "VEN003", "Carlos", "Rodríguez Vega", "987654323", "carlos.rodriguez@distribuidora.com"),
        ("55443322", "VEN004", "Ana", "Torres Silva", "987654324", "ana.torres@distribuidora.com"),
        ("66778899", "VEN005", "Luis", "Mendoza Castro", "987654325", "luis.mendoza@distribuidora.com")
    ]
    
    # Evaluadores  
    evaluadores = [
        ("22334455", "EVA001", "Ana", "Martínez Silva", "987654330", "ana.martinez@distribuidora.com"),
        ("33445566", "EVA002", "Luis", "Fernández Torres", "987654331", "luis.fernandez@distribuidora.com"),
        ("44556677", "EVA003", "Carmen", "López Herrera", "987654332", "carmen.lopez@distribuidora.com")
    ]
    
    # Supervisores
    supervisores = [
        ("44556677", "SUP001", "Roberto", "Jiménez Castro", "987654340", "roberto.jimenez@distribuidora.com"),
        ("55667788", "SUP002", "Carmen", "López Herrera", "987654341", "carmen.lopez@distribuidora.com")
    ]
    
    with engine.begin() as conn:
        # Limpiar usuarios existentes en Railway
        if IS_RAILWAY:
            conn.execute(text("DELETE FROM sesiones_activas"))
            conn.execute(text("DELETE FROM vendedores"))
            conn.execute(text("DELETE FROM evaluadores")) 
            conn.execute(text("DELETE FROM supervisores"))
        
        # Insertar vendedores
        for dni, codigo, nombre, apellidos, telefono, email in vendedores:
            password_hash = hash_password(dni)  # Password = DNI
            
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM vendedores WHERE dni = :dni)
            """), {"dni": dni}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO vendedores (
                        dni, codigo_vendedor, nombre, apellidos, telefono, email,
                        password_hash, activo, verificado, distrito, provincia, departamento
                    ) VALUES (
                        :dni, :codigo, :nombre, :apellidos, :telefono, :email,
                        :password_hash, true, true, 'Lima', 'Lima', 'Lima'
                    )
                """), {
                    "dni": dni, "codigo": codigo, "nombre": nombre, "apellidos": apellidos,
                    "telefono": telefono, "email": email, "password_hash": password_hash
                })
                print(f"✅ Vendedor creado: {nombre} {apellidos} (DNI: {dni})")
        
        # Insertar evaluadores
        for dni, codigo, nombre, apellidos, telefono, email in evaluadores:
            password_hash = hash_password(dni)  # Password = DNI
            
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM evaluadores WHERE dni = :dni)
            """), {"dni": dni}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO evaluadores (
                        dni, codigo_evaluador, nombre, apellidos, telefono, email,
                        password_hash, activo, verificado, distrito_asignado, provincia_asignada, departamento_asignado
                    ) VALUES (
                        :dni, :codigo, :nombre, :apellidos, :telefono, :email,
                        :password_hash, true, true, 'Lima', 'Lima', 'Lima'
                    )
                """), {
                    "dni": dni, "codigo": codigo, "nombre": nombre, "apellidos": apellidos,
                    "telefono": telefono, "email": email, "password_hash": password_hash
                })
                print(f"✅ Evaluador creado: {nombre} {apellidos} (DNI: {dni})")
        
        # Insertar supervisores
        for dni, codigo, nombre, apellidos, telefono, email in supervisores:
            password_hash = hash_password(dni)  # Password = DNI
            
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM supervisores WHERE dni = :dni)
            """), {"dni": dni}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO supervisores (
                        dni, codigo_supervisor, nombre, apellidos, telefono, email,
                        password_hash, activo, verificado, cargo, nivel_acceso
                    ) VALUES (
                        :dni, :codigo, :nombre, :apellidos, :telefono, :email,
                        :password_hash, true, true, 'Supervisor', 'supervisor'
                    )
                """), {
                    "dni": dni, "codigo": codigo, "nombre": nombre, "apellidos": apellidos,
                    "telefono": telefono, "email": email, "password_hash": password_hash
                })
                print(f"✅ Supervisor creado: {nombre} {apellidos} (DNI: {dni})")

def crear_clientes_muestra():
    """Crea clientes de muestra"""
    
    def crear_clientes_muestra():
        # Fix directo - crear tipos si no existen
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO tipos_cliente (nombre, descripcion) VALUES ('bodega', 'Bodegas') ON CONFLICT (nombre) DO NOTHING"))
            conn.execute(text("INSERT INTO tipos_cliente (nombre, descripcion) VALUES ('minimarket', 'Minimarkets') ON CONFLICT (nombre) DO NOTHING"))
            conn.execute(text("INSERT INTO tipos_cliente (nombre, descripcion) VALUES ('restaurante', 'Restaurantes') ON CONFLICT (nombre) DO NOTHING"))
            conn.execute(text("INSERT INTO tipos_cliente (nombre, descripcion) VALUES ('mayorista', 'Mayoristas') ON CONFLICT (nombre) DO NOTHING"))
    
    print("🏪 Creando clientes de muestra...")
    
    clientes = [
        ("CLI001", "Bodega San Martín", "Bodega San Martín E.I.R.L.", "20123456781", "987654401", 1),
        ("CLI002", "Minimarket El Sol", "Minimarket El Sol S.A.C.", "20987654321", "987654402", 2),
        ("CLI003", "Restaurante La Plaza", "Restaurante La Plaza S.R.L.", "20456789123", "987654403", 3),
        ("CLI004", "Distribuidora Norte", "Distribuidora Norte S.A.", "20789123456", "987654404", 4),
        ("CLI005", "Bodega Doña María", None, None, "987654405", 1),
        ("CLI006", "Market Central", "Market Central E.I.R.L.", "20321654987", "987654406", 2),
        ("CLI007", "Pollería El Rancho", "Pollería El Rancho S.A.C.", "20147258369", "987654407", 3),
        ("CLI008", "Tienda La Esquina", None, None, "987654408", 1)
    ]
    
    with engine.begin() as conn:
        for codigo, nombre, razon, ruc, telefono, tipo_cliente in clientes:
            exists = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM clientes WHERE codigo_cliente = :codigo)
            """), {"codigo": codigo}).scalar()
            
            if not exists:
                conn.execute(text("""
                    INSERT INTO clientes (
                        codigo_cliente, nombre_comercial, razon_social, ruc, telefono,
                        direccion_completa, distrito, provincia, departamento, 
                        activo, verificado, tipo_cliente_id
                    ) VALUES (
                        :codigo, :nombre, :razon, :ruc, :telefono,
                        'Dirección de ejemplo', 'Lima', 'Lima', 'Lima',
                        true, true, :tipo_cliente
                    )
                """), {
                    "codigo": codigo, "nombre": nombre, "razon": razon, "ruc": ruc,
                    "telefono": telefono, "tipo_cliente": tipo_cliente
                })
                print(f"✅ Cliente creado: {nombre}")

# PRODUCTOS DE ABARROTES (primeros 50 para no saturar)
PRODUCTOS_ABARROTES = [
    ("Aceite Vegetal Primor 1L", "7754800100014", "unidad", 8.50, "Aceite vegetal refinado de primera calidad"),
    ("Arroz Superior Paisana 1kg", "7751234001011", "unidad", 4.20, "Arroz blanco grano largo"),
    ("Azúcar Rubia Cartavio 1kg", "7751271050011", "unidad", 3.80, "Azúcar rubia refinada"),
    ("Fideos Espagueti Don Vittorio 500g", "7751271070011", "unidad", 2.80, "Pasta espagueti premium"),
    ("Harina Blanca Nicolini 1kg", "7751271080011", "unidad", 3.50, "Harina de trigo sin preparar"),
    ("Atún Primor Agua 170g", "7751271090011", "unidad", 4.50, "Atún en agua bajo en sal"),
    ("Lentejas Pardinas 500g", "7751234010011", "unidad", 4.50, "Lentejas secas seleccionadas"),
    ("Sal de Mesa Emsal 1kg", "7751271100011", "unidad", 1.80, "Sal yodada fluorada"),
    ("Sopa Instantánea Maggi Pollo 70g", "7613033479011", "unidad", 1.80, "Sopa instantánea sabor pollo"),
    ("Salsa de Tomate Libby's 340g", "7411000320011", "unidad", 3.50, "Salsa de tomate clásica"),
    ("Galletas Soda Margarita 6pk", "7751271120011", "unidad", 3.20, "Galletas soda saladas"),
    ("Café Altomayo Molido 250g", "7751234025011", "unidad", 12.50, "Café molido 100% arábica"),
    ("Leche Evaporada Gloria 400g", "7751271130011", "unidad", 3.80, "Leche evaporada entera"),
    ("Pan Tostado Bimbo Integral 350g", "7441001010011", "unidad", 5.80, "Pan tostado integral en rebanadas"),
    ("Papas Lays Clásicas 140g", "7751234030011", "unidad", 4.50, "Papas fritas clásicas"),
    ("Quinua Tricolor 500g", "7751234040011", "unidad", 14.50, "Quinua roja, negra y blanca"),
    ("Aceite de Oliva Borges 500ml", "8410161105011", "unidad", 22.90, "Aceite de oliva extra virgen importado"),
    ("Vinagre Blanco Bells 500ml", "7751234500011", "unidad", 3.50, "Vinagre blanco de mesa"),
    ("Avena Quaker 200g", "7501000118014", "unidad", 4.80, "Avena en hojuelas instantánea"),
    ("Quinua Real Andina 500g", "7751234004041", "unidad", 12.50, "Quinua blanca andina"),
    ("Fideos Corbata Molitalia 500g", "7751271071021", "unidad", 2.50, "Pasta corbata clásica"),
    ("Maicena Maizorsa 180g", "7751271082031", "unidad", 2.80, "Fécula de maíz pura"),
    ("Sardinas Campomar 425g", "7751271092031", "unidad", 6.80, "Sardinas en salsa de tomate"),
    ("Frijoles Canarios 500g", "7751234011021", "unidad", 5.20, "Frijoles canarios peruanos"),
    ("Comino Molido Sibarita 50g", "7751271102031", "unidad", 3.80, "Comino molido aromático"),
    ("Ketchup Heinz 567g", "7622210947011", "unidad", 8.90, "Salsa de tomate dulce"),
    ("Galletas Chocochips Morochas 6pk", "7751271121021", "unidad", 4.50, "Galletas con chips de chocolate"),
    ("Café Nescafé Clásico 170g", "7613036470011", "unidad", 18.90, "Café soluble premium"),
    ("Leche Condensada Nestlé 393g", "7613031220011", "unidad", 5.50, "Leche condensada azucarada"),
    ("Chifles Inka Chips 100g", "7751234032031", "unidad", 3.80, "Plátano frito en hojuelas")
]

# PRODUCTOS DE BEBIDAS (primeros 30)
PRODUCTOS_BEBIDAS = [
    ("Coca Cola Original 500ml", "7751271000021", "unidad", 3.20, "Bebida gaseosa cola 500ml botella"),
    ("Inca Kola Original 500ml", "7751271020021", "unidad", 3.20, "Bebida gaseosa sabor único 500ml"),
    ("Sprite Original 500ml", "7751271030021", "unidad", 3.20, "Bebida gaseosa lima limón 500ml"),
    ("Agua San Luis 625ml", "7751271300014", "unidad", 1.50, "Agua de mesa sin gas 625ml"),
    ("Fanta Naranja 500ml", "7751271040021", "unidad", 3.20, "Bebida gaseosa sabor naranja 500ml"),
    ("Coca Cola Original 1.5L", "7751271000045", "unidad", 6.50, "Bebida gaseosa cola 1.5 litros"),
    ("Inca Kola Original 1.5L", "7751271020045", "unidad", 6.50, "Bebida gaseosa sabor único 1.5L"),
    ("Agua San Luis 1.5L", "7751271300021", "unidad", 2.80, "Agua de mesa sin gas 1.5L"),
    ("Pepsi Cola 500ml", "7751271200021", "unidad", 3.20, "Bebida gaseosa cola 500ml"),
    ("Jugo Frugos Durazno 1L", "7751271500014", "unidad", 5.80, "Jugo de durazno con pulpa"),
    ("Cerveza Pilsen Callao 330ml", "7751271600014", "unidad", 4.50, "Cerveza rubia nacional 330ml"),
    ("Red Bull Energy 250ml", "9002490100014", "unidad", 8.50, "Bebida energética original"),
    ("Powerade Azul 500ml", "7751271410021", "unidad", 4.20, "Bebida isotónica azul"),
    ("Agua Cielo 625ml", "7751271310014", "unidad", 1.50, "Agua purificada 625ml"),
    ("Sprite Original 1.5L", "7751271030045", "unidad", 6.50, "Bebida gaseosa lima limón 1.5L"),
    ("Fanta Naranja 1.5L", "7751271040045", "unidad", 6.50, "Bebida gaseosa sabor naranja 1.5L"),
    ("Jugo Frugos Mango 1L", "7751271501014", "unidad", 5.80, "Jugo de mango con pulpa"),
    ("Cerveza Cristal 330ml", "7751271610014", "unidad", 4.50, "Cerveza rubia premium 330ml"),
    ("Gatorade Naranja 500ml", "7751271420021", "unidad", 4.50, "Bebida deportiva naranja"),
    ("Kola Real Original 500ml", "7751271210021", "unidad", 2.80, "Bebida gaseosa nacional 500ml")
]

def limpiar_productos_existentes():
    """Elimina productos y precios existentes"""
    with engine.begin() as conn:
        print("🗑️ Limpiando productos existentes...")
        conn.execute(text("DELETE FROM precios"))
        conn.execute(text("DELETE FROM productos"))
        print("✅ Productos y precios eliminados")

def calcular_precios_diferenciados(precio_base):
    """Calcula precios diferenciados por tipo de cliente"""
    precio_bodega = float(precio_base)
    precio_minimarket = precio_bodega * 0.95
    precio_restaurante = precio_bodega
    precio_mayorista = precio_bodega * 0.85
    
    return {
        1: round(precio_bodega, 2),
        2: round(precio_minimarket, 2),
        3: round(precio_restaurante, 2),
        4: round(precio_mayorista, 2)
    }

def insertar_productos():
    """Inserta productos de abarrotes y bebidas"""
    print("🛒 Insertando productos...")
    
    with engine.begin() as conn:
        productos_insertados = 0
        precios_insertados = 0
        
        # Productos de abarrotes
        for nombre, codigo_barras, unidad, precio_base, descripcion in PRODUCTOS_ABARROTES:
            codigo_producto = f"ABR{productos_insertados + 1:03d}"
            
            result = conn.execute(text("""
                INSERT INTO productos (
                    codigo_producto, codigo_barras, nombre, descripcion, 
                    categoria_id, unidad_medida, precio_unitario,
                    stock_minimo, stock_actual, activo, destacado
                ) VALUES (
                    :codigo, :barras, :nombre, :desc,
                    2, :unidad, :precio,
                    :stock_min, :stock_actual, true, :destacado
                ) RETURNING id
            """), {
                "codigo": codigo_producto,
                "barras": codigo_barras,
                "nombre": nombre,
                "desc": descripcion,
                "unidad": unidad,
                "precio": precio_base,
                "stock_min": random.randint(10, 50),
                "stock_actual": random.randint(20, 200),
                "destacado": random.choice([True, False, False, False])
            })
            
            producto_id = result.fetchone()[0]
            productos_insertados += 1
            
            # Insertar precios diferenciados
            precios = calcular_precios_diferenciados(precio_base)
            for tipo_cliente_id, precio in precios.items():
                conn.execute(text("""
                    INSERT INTO precios (producto_id, tipo_cliente_id, precio)
                    VALUES (:producto_id, :tipo_cliente, :precio)
                """), {
                    "producto_id": producto_id,
                    "tipo_cliente": tipo_cliente_id,
                    "precio": precio
                })
                precios_insertados += 1
        
        # Productos de bebidas
        for nombre, codigo_barras, unidad, precio_base, descripcion in PRODUCTOS_BEBIDAS:
            codigo_producto = f"BEB{productos_insertados - len(PRODUCTOS_ABARROTES) + 1:03d}"
            
            result = conn.execute(text("""
                INSERT INTO productos (
                    codigo_producto, codigo_barras, nombre, descripcion, 
                    categoria_id, unidad_medida, precio_unitario,
                    stock_minimo, stock_actual, activo, destacado
                ) VALUES (
                    :codigo, :barras, :nombre, :desc,
                    1, :unidad, :precio,
                    :stock_min, :stock_actual, true, :destacado
                ) RETURNING id
            """), {
                "codigo": codigo_producto,
                "barras": codigo_barras,
                "nombre": nombre,
                "desc": descripcion,
                "unidad": unidad,
                "precio": precio_base,
                "stock_min": random.randint(5, 30),
                "stock_actual": random.randint(10, 150),
                "destacado": random.choice([True, False, False, False])
            })
            
            producto_id = result.fetchone()[0]
            productos_insertados += 1
            
            # Insertar precios diferenciados
            precios = calcular_precios_diferenciados(precio_base)
            for tipo_cliente_id, precio in precios.items():
                conn.execute(text("""
                    INSERT INTO precios (producto_id, tipo_cliente_id, precio)
                    VALUES (:producto_id, :tipo_cliente, :precio)
                """), {
                    "producto_id": producto_id,
                    "tipo_cliente": tipo_cliente_id,
                    "precio": precio
                })
                precios_insertados += 1
        
        print(f"✅ {productos_insertados} productos insertados")
        print(f"✅ {precios_insertados} precios insertados")

def mostrar_estadisticas():
    """Muestra estadísticas finales"""
    print("\n" + "=" * 50)
    print("📊 ESTADÍSTICAS FINALES")
    print("=" * 50)
    
    with engine.connect() as conn:
        vendedores = conn.execute(text("SELECT COUNT(*) FROM vendedores")).scalar()
        evaluadores = conn.execute(text("SELECT COUNT(*) FROM evaluadores")).scalar()
        supervisores = conn.execute(text("SELECT COUNT(*) FROM supervisores")).scalar()
        clientes = conn.execute(text("SELECT COUNT(*) FROM clientes")).scalar()
        productos = conn.execute(text("SELECT COUNT(*) FROM productos")).scalar()
        precios = conn.execute(text("SELECT COUNT(*) FROM precios")).scalar()
        
        print(f"👥 Vendedores: {vendedores}")
        print(f"👤 Evaluadores: {evaluadores}")
        print(f"👨‍💼 Supervisores: {supervisores}")
        print(f"🏪 Clientes: {clientes}")
        print(f"📦 Productos: {productos}")
        print(f"💰 Precios: {precios}")

if __name__ == "__main__":
    try:
        print("🚀 SEEDER COMPLETO PARA RAILWAY")
        print("=" * 50)
        print(f"Entorno: {'Railway' if IS_RAILWAY else 'Local'}")
        print(f"Base de datos: {DATABASE_URL[:50]}...")
        
        # Ejecutar en orden
        verificar_y_crear_categorias()
        crear_usuarios_base()
        crear_clientes_muestra()
        
        # Solo limpiar productos en Railway
        if IS_RAILWAY:
            limpiar_productos_existentes()
        
        insertar_productos()
        mostrar_estadisticas()
        
        print("\n✅ SEEDER COMPLETADO EXITOSAMENTE")
        print("🎯 Sistema listo para demo")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if not IS_RAILWAY:
            print("\n🔧 Verificar conexión a base de datos local")


