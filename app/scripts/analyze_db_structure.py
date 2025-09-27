# analyze_db_structure.py

#No probado aun:
"""
cd C:\PEDIDOS
python -m app.scripts.analyze_db_structure
"""

import inspect
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import engine, Base
from models import *  # Importar todos los modelos

def analyze_database_structure():
    """Analiza la estructura completa de la base de datos"""
    
    print("=" * 80)
    print("📊 ANÁLISIS DE ESTRUCTURA DE BASE DE DATOS")
    print("=" * 80)
    
    # 1. LISTAR TODAS LAS TABLAS
    print("\n🗂️  TABLAS EN LA BASE DE DATOS:")
    print("-" * 50)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        for i, table in enumerate(tables, 1):
            print(f"{i:2d}. {table}")
    
    print(f"\n📊 Total de tablas: {len(tables)}")
    
    # 2. ESTRUCTURA DETALLADA POR TABLA
    print("\n" + "=" * 80)
    print("📋 ESTRUCTURA DETALLADA DE CADA TABLA")
    print("=" * 80)
    
    for table in tables:
        print(f"\n🔸 TABLA: {table.upper()}")
        print("-" * 60)
        
        with engine.connect() as conn:
            # Obtener columnas
            result = conn.execute(text(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            print("Columnas:")
            for col in columns:
                col_name, data_type, nullable, default, max_length = col
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                length_str = f"({max_length})" if max_length else ""
                default_str = f" DEFAULT {default}" if default else ""
                
                print(f"  • {col_name:<25} {data_type}{length_str:<15} {nullable_str}{default_str}")
            
            # Obtener claves foráneas
            fk_result = conn.execute(text(f"""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.key_column_usage kcu
                JOIN information_schema.constraint_column_usage ccu
                    ON kcu.constraint_name = ccu.constraint_name
                WHERE kcu.table_name = '{table}'
                    AND EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        WHERE tc.constraint_name = kcu.constraint_name
                        AND tc.constraint_type = 'FOREIGN KEY'
                    );
            """))
            
            foreign_keys = fk_result.fetchall()
            if foreign_keys:
                print("\nClaves Foráneas:")
                for fk in foreign_keys:
                    col_name, ref_table, ref_col = fk
                    print(f"  • {col_name} → {ref_table}.{ref_col}")

def analyze_models():
    """Analiza los modelos SQLAlchemy"""
    
    print("\n" + "=" * 80)
    print("🏗️  MODELOS SQLALCHEMY")
    print("=" * 80)
    
    # Obtener todas las clases que heredan de Base
    models = []
    for name, obj in globals().items():
        if (inspect.isclass(obj) and 
            hasattr(obj, '__tablename__') and 
            issubclass(obj, Base)):
            models.append((name, obj))
    
    for model_name, model_class in sorted(models):
        print(f"\n🔸 MODELO: {model_name}")
        print("-" * 50)
        print(f"Tabla: {model_class.__tablename__}")
        
        # Obtener columnas del modelo
        if hasattr(model_class, '__table__'):
            print("Columnas:")
            for column in model_class.__table__.columns:
                print(f"  • {column.name:<20} {str(column.type):<15} {column}")
            
            # Relaciones
            if hasattr(model_class, '__mapper__'):
                relationships = model_class.__mapper__.relationships
                if relationships:
                    print("Relaciones:")
                    for rel_name, rel in relationships.items():
                        print(f"  • {rel_name} → {rel.entity.class_.__name__}")

def analyze_key_tables():
    """Analiza tablas clave para productos"""
    
    print("\n" + "=" * 80)
    print("🛍️  ANÁLISIS DE TABLAS DE PRODUCTOS")
    print("=" * 80)
    
    key_tables = [
        'productos', 'categorias', 'marcas', 'unidades_medida', 
        'variantes', 'precios', 'producto_precios', 'tipos_cliente'
    ]
    
    with engine.connect() as conn:
        for table in key_tables:
            # Verificar si la tabla existe
            exists = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{table}'
                );
            """)).scalar()
            
            if exists:
                print(f"\n✅ TABLA: {table}")
                
                # Contar registros
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"Registros actuales: {count}")
                
                # Mostrar algunos ejemplos
                if count > 0:
                    result = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    print("Ejemplos:")
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        print(f"  {row_dict}")
            else:
                print(f"\n❌ TABLA NO EXISTE: {table}")

def generate_insert_examples():
    """Genera ejemplos de inserts para entender la estructura"""
    
    print("\n" + "=" * 80)
    print("💾 EJEMPLOS DE ESTRUCTURA PARA INSERTS")
    print("=" * 80)
    
    examples = {
        'productos': {
            'descripcion': 'Ejemplo de producto',
            'codigo_barra': '7751234567890',
            'categoria_id': 1,
            'marca_id': 1,
            'activo': True
        },
        'variantes': {
            'producto_id': 1,
            'nombre_variante': 'Unidad',
            'unidad_medida': 'UND',
            'factor_conversion': 1.0,
            'activo': True
        },
        'precios': {
            'variante_id': 1,
            'tipo_cliente': 'mayorista',
            'precio_unitario': 2.50,
            'fecha_vigencia': '2025-01-01'
        }
    }
    
    for table, example in examples.items():
        print(f"\n📝 Ejemplo INSERT para {table}:")
        columns = ', '.join(example.keys())
        values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in example.values()])
        print(f"INSERT INTO {table} ({columns}) VALUES ({values});")

if __name__ == "__main__":
    try:
        analyze_database_structure()
        analyze_models()
        analyze_key_tables()
        generate_insert_examples()
        
        print("\n" + "=" * 80)
        print("✅ ANÁLISIS COMPLETADO")
        print("=" * 80)
        print("\nUsa esta información para generar los datos de productos.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nAsegúrate de que:")
        print("1. La base de datos esté corriendo")
        print("2. Los modelos estén importados correctamente")
        print("3. Las tablas existan en la BD")