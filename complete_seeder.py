# complete_seeder.py - FINAL CON TODOS LOS DATOS
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
import random
from decimal import Decimal
from dotenv import load_dotenv
import bcrypt
from datetime import datetime, timedelta

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

def crear_tipos_cliente_forzado():
    """Crea tipos de cliente de forma directa"""
    print("🏷️ Insertando tipos de cliente...")
    
    with engine.begin() as conn:
        # Eliminar existentes y recrear
        conn.execute(text("DELETE FROM tipos_cliente"))
        
        # Insertar directamente
        conn.execute(text("""
            INSERT INTO tipos_cliente (id, nombre, descripcion, activo) VALUES 
            (1, 'bodega', 'Precio minorista para bodegas', true),
            (2, 'minimarket', 'Precio para minimarkets', true),
            (3, 'restaurante', 'Precio para restaurantes', true),
            (4, 'mayorista', 'Precio mayorista', true)
        """))
        
        # Resetear secuencia
        conn.execute(text("SELECT setval('tipos_cliente_id_seq', 4, true)"))
        
        print("✅ Tipos de cliente creados con IDs fijos")

def crear_categorias_forzado():
    """Crea categorías de forma directa"""
    print("📁 Insertando categorías...")
    
    with engine.begin() as conn:
        # Eliminar existentes
        conn.execute(text("DELETE FROM categorias"))
        
        # Insertar directamente
        conn.execute(text("""
            INSERT INTO categorias (categoria_id, nombre, codigo_categoria, descripcion, activa) VALUES 
            (1, 'Bebidas', 'BEB', 'Bebidas gaseosas, jugos, agua', true),
            (2, 'Abarrotes', 'ABR', 'Productos de abarrotes', true),
            (3, 'Snacks', 'SNK', 'Galletas, papas fritas, dulces', true),
            (4, 'Lácteos', 'LAC', 'Leche, quesos, yogurt', true)
        """))
        
        # Resetear secuencia
        conn.execute(text("SELECT setval('categorias_categoria_id_seq', 4, true)"))
        
        print("✅ Categorías creadas con IDs fijos")

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
        ("77889900", "SUP001", "Roberto", "Jiménez Castro", "987654340", "roberto.jimenez@distribuidora.com"),
        ("55667788", "SUP002", "Patricia", "Vega Morales", "987654341", "patricia.vega@distribuidora.com")
    ]
    
    with engine.begin() as conn:
        # Limpiar usuarios existentes
        conn.execute(text("DELETE FROM vendedores"))
        conn.execute(text("DELETE FROM evaluadores"))
        conn.execute(text("DELETE FROM supervisores"))
        
        # Insertar vendedores
        for dni, codigo, nombre, apellidos, telefono, email in vendedores:
            password_hash = hash_password(dni)  # Password = DNI
            
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
    print("🏪 Creando clientes de muestra...")
    
    clientes = [
        ("CLI001", "Bodega San Martín", "Bodega San Martín E.I.R.L.", "20123456781", "987654401", 1),
        ("CLI002", "Minimarket El Sol", "Minimarket El Sol S.A.C.", "20987654321", "987654402", 2),
        ("CLI003", "Restaurante La Plaza", "Restaurante La Plaza S.R.L.", "20456789123", "987654403", 3),
        ("CLI004", "Distribuidora Norte", "Distribuidora Norte S.A.", "20789123456", "987654404", 4),
        ("CLI005", "Bodega Doña María", None, None, "987654405", 1),
        ("CLI006", "Market Central", "Market Central E.I.R.L.", "20321654987", "987654406", 2),
        ("CLI007", "Pollería El Rancho", "Pollería El Rancho S.A.C.", "20147258369", "987654407", 3),
        ("CLI008", "Tienda La Esquina", None, None, "987654408", 1),
        ("CLI009", "Supermercado Familiar", "Supermercado Familiar S.A.", "20555666777", "987654409", 2),
        ("CLI010", "Restaurant El Sabor", "Restaurant El Sabor E.I.R.L.", "20888999000", "987654410", 3)
    ]
    
    with engine.begin() as conn:
        # Limpiar clientes existentes
        conn.execute(text("DELETE FROM clientes"))
        
        for codigo, nombre, razon, ruc, telefono, tipo_cliente in clientes:
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

# PRODUCTOS PARA LA DEMO
PRODUCTOS_ABARROTES = [
    ("Aceite Vegetal Primor 1L", "7754800100014", "unidad", 8.50, "Aceite vegetal refinado"),
    ("Arroz Superior Paisana 1kg", "7751234001011", "unidad", 4.20, "Arroz blanco grano largo"),
    ("Azúcar Rubia Cartavio 1kg", "7751271050011", "unidad", 3.80, "Azúcar rubia refinada"),
    ("Fideos Espagueti Don Vittorio 500g", "7751271070011", "unidad", 2.80, "Pasta espagueti premium"),
    ("Atún Primor Agua 170g", "7751271090011", "unidad", 4.50, "Atún en agua bajo en sal"),
    ("Lentejas Pardinas 500g", "7751234010011", "unidad", 4.50, "Lentejas secas seleccionadas"),
    ("Sal de Mesa Emsal 1kg", "7751271100011", "unidad", 1.80, "Sal yodada fluorada"),
    ("Galletas Soda Margarita 6pk", "7751271120011", "unidad", 3.20, "Galletas soda saladas"),
    ("Café Altomayo Molido 250g", "7751234025011", "unidad", 12.50, "Café molido 100% arábica"),
    ("Leche Evaporada Gloria 400g", "7751271130011", "unidad", 3.80, "Leche evaporada entera"),
    ("Harina Blanca Nicolini 1kg", "7751271080011", "unidad", 3.50, "Harina de trigo sin preparar"),
    ("Conserva Durazno Aconcagua 820g", "7751271093041", "unidad", 7.90, "Duraznos en almíbar"),
    ("Mayonesa Alacena 475g", "7751271110011", "unidad", 6.20, "Mayonesa cremosa tradicional"),
    ("Salsa de Tomate Libby's 340g", "7411000320011", "unidad", 3.50, "Salsa de tomate clásica"),
    ("Frijoles Canarios 500g", "7751234011021", "unidad", 5.20, "Frijoles canarios peruanos")
]

PRODUCTOS_BEBIDAS = [
    ("Coca Cola Original 500ml", "7751271000021", "unidad", 3.20, "Bebida gaseosa cola 500ml"),
    ("Inca Kola Original 500ml", "7751271020021", "unidad", 3.20, "Bebida gaseosa sabor único"),
    ("Sprite Original 500ml", "7751271030021", "unidad", 3.20, "Bebida gaseosa lima limón"),
    ("Agua San Luis 625ml", "7751271300014", "unidad", 1.50, "Agua de mesa sin gas"),
    ("Fanta Naranja 500ml", "7751271040021", "unidad", 3.20, "Bebida gaseosa sabor naranja"),
    ("Cerveza Pilsen Callao 330ml", "7751271600014", "unidad", 4.50, "Cerveza rubia nacional"),
    ("Red Bull Energy 250ml", "9002490100014", "unidad", 8.50, "Bebida energética original"),
    ("Jugo Frugos Durazno 1L", "7751271500014", "unidad", 5.80, "Jugo de durazno con pulpa"),
    ("Powerade Azul 500ml", "7751271410021", "unidad", 4.20, "Bebida isotónica azul"),
    ("Agua Cielo 625ml", "7751271310014", "unidad", 1.50, "Agua purificada"),
    ("Coca Cola Original 1.5L", "7751271000045", "unidad", 6.50, "Bebida gaseosa cola 1.5L"),
    ("Inca Kola Original 1.5L", "7751271020045", "unidad", 6.50, "Bebida gaseosa sabor único 1.5L"),
    ("Cerveza Cristal 330ml", "7751271610014", "unidad", 4.50, "Cerveza rubia premium"),
    ("Gatorade Naranja 500ml", "7751271420021", "unidad", 4.50, "Bebida deportiva naranja"),
    ("Jugo Frugos Mango 1L", "7751271501014", "unidad", 5.80, "Jugo de mango con pulpa")
]

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
        # Limpiar productos y precios existentes
        conn.execute(text("DELETE FROM precios"))
        conn.execute(text("DELETE FROM productos"))
        
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

def crear_pedidos_muestra():
    """Crea pedidos de muestra para el dashboard del vendedor"""
    print("📋 Creando pedidos de muestra...")
    
    with engine.begin() as conn:
        # Limpiar pedidos existentes
        conn.execute(text("DELETE FROM pedido_items"))
        conn.execute(text("DELETE FROM pedidos"))
        
        # Obtener IDs de vendedores, clientes y productos
        vendedores = conn.execute(text("SELECT vendedor_id FROM vendedores LIMIT 5")).fetchall()
        clientes = conn.execute(text("SELECT id FROM clientes LIMIT 10")).fetchall()
        productos = conn.execute(text("SELECT id, precio_unitario FROM productos")).fetchall()
        
        if not vendedores or not clientes or not productos:
            print("❌ No hay suficientes datos para crear pedidos")
            return
        
        estados_pedido = ['pendiente_aprobacion', 'aprobado', 'rechazado', 'en_proceso', 'entregado']
        metodos_pago = ['efectivo', 'credito', 'transferencia']
        
        pedidos_creados = 0
        items_creados = 0
        
        # Crear 20 pedidos de muestra
        for i in range(20):
            vendedor_id = random.choice(vendedores)[0]
            cliente_id = random.choice(clientes)[0]
            estado = random.choice(estados_pedido)
            metodo_pago = random.choice(metodos_pago)
            
            # Fecha aleatoria en los últimos 30 días
            fecha_creacion = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # Insertar pedido
            result = conn.execute(text("""
                INSERT INTO pedidos (
                    codigo_pedido, cliente_id, vendedor_id, fecha_creacion,
                    monto_total, metodo_pago, estado, observaciones
                ) VALUES (
                    :codigo, :cliente_id, :vendedor_id, :fecha_creacion,
                    :monto_total, :metodo_pago, :estado, :observaciones
                ) RETURNING id
            """), {
                "codigo": f"PED-{fecha_creacion.strftime('%Y%m%d')}-{i+1:03d}",
                "cliente_id": cliente_id,
                "vendedor_id": vendedor_id,
                "fecha_creacion": fecha_creacion,
                "monto_total": 0,  # Se calculará después
                "metodo_pago": metodo_pago,
                "estado": estado,
                "observaciones": f"Pedido de muestra #{i+1}"
            })
            
            pedido_id = result.fetchone()[0]
            pedidos_creados += 1
            
            # Agregar 2-5 productos al pedido
            num_productos = random.randint(2, 5)
            monto_total = 0
            
            productos_pedido = random.sample(productos, min(num_productos, len(productos)))
            
            for producto_id, precio_unitario in productos_pedido:
                cantidad = random.randint(1, 10)
                precio_venta = float(precio_unitario) * random.uniform(0.95, 1.05)  # Variación del 5%
                subtotal = cantidad * precio_venta
                monto_total += subtotal
                
                conn.execute(text("""
                    INSERT INTO pedido_items (
                        pedido_id, producto_id, unidad_medida_venta,
                        cantidad, precio_unitario_venta, subtotal
                    ) VALUES (
                        :pedido_id, :producto_id, 'unidad',
                        :cantidad, :precio_unitario, :subtotal
                    )
                """), {
                    "pedido_id": pedido_id,
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unitario": precio_venta,
                    "subtotal": subtotal
                })
                items_creados += 1
            
            # Actualizar monto total del pedido
            conn.execute(text("""
                UPDATE pedidos SET monto_total = :monto_total WHERE id = :pedido_id
            """), {
                "monto_total": round(monto_total, 2),
                "pedido_id": pedido_id
            })
        
        print(f"✅ {pedidos_creados} pedidos creados")
        print(f"✅ {items_creados} items de pedido creados")

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
        pedidos = conn.execute(text("SELECT COUNT(*) FROM pedidos")).scalar()
        pedido_items = conn.execute(text("SELECT COUNT(*) FROM pedido_items")).scalar()
        
        print(f"👥 Vendedores: {vendedores}")
        print(f"👤 Evaluadores: {evaluadores}")
        print(f"👨‍💼 Supervisores: {supervisores}")
        print(f"🏪 Clientes: {clientes}")
        print(f"📦 Productos: {productos}")
        print(f"💰 Precios: {precios}")
        print(f"📋 Pedidos: {pedidos}")
        print(f"📝 Items de pedido: {pedido_items}")

if __name__ == "__main__":
    try:
        print("🚀 SEEDER COMPLETO CON PEDIDOS")
        print("=" * 50)
        print(f"Entorno: {'Railway' if IS_RAILWAY else 'Local'}")
        print(f"Database: {DATABASE_URL[:50]}...")
        
        # Ejecutar en orden correcto
        print("\nPaso 1: Tipos de cliente")
        crear_tipos_cliente_forzado()
        
        print("\nPaso 2: Categorías")
        crear_categorias_forzado()
        
        print("\nPaso 3: Usuarios")
        crear_usuarios_base()
        
        print("\nPaso 4: Clientes")
        crear_clientes_muestra()
        
        print("\nPaso 5: Productos y precios")
        insertar_productos()
        
        print("\nPaso 6: Pedidos de muestra")
        crear_pedidos_muestra()
        
        mostrar_estadisticas()
        
        print("\n✅ SEEDER COMPLETADO EXITOSAMENTE")
        print("🎯 Sistema listo para demo completa")
        print("\n📋 USUARIOS DE PRUEBA:")
        print("Vendedor: DNI 12345678 / Pass: 12345678")
        print("Evaluador: DNI 22334455 / Pass: 22334455") 
        print("Supervisor: DNI 77889900 / Pass: 77889900")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
