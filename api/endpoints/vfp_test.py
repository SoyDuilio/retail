from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.product_models import ProductoModel

router = APIRouter()

# Token simple para VFP (temporal para pruebas)
VFP_TEST_TOKEN = "vfp_test_2024_pedidos_secret"

def verificar_token_vfp(authorization: Optional[str] = Header(None)):
    """Verificar token para VFP"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    if authorization != f"Bearer {VFP_TEST_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return True

# ============================================
# PRUEBA 1: CONEXIÓN (PING)
# ============================================
@router.get("/api/vfp/test/ping")
async def test_ping(token_ok: bool = Depends(verificar_token_vfp)):
    """Prueba básica de conexión"""
    return {
        "success": True,
        "message": "Conexión exitosa desde VFP",
        "timestamp": "2024-01-01 10:00:00"
    }

# ============================================
# PRUEBA 2: CONSULTA (GET)
# ============================================
@router.get("/api/vfp/test/productos")
async def test_consulta_productos(
    limite: int = 10,
    token_ok: bool = Depends(verificar_token_vfp),
    db: Session = Depends(get_db)
):
    """Obtener lista de productos"""
    try:
        productos = db.query(ProductoModel).filter(
            ProductoModel.activo == True
        ).limit(limite).all()
        
        resultado = []
        for p in productos:
            resultado.append({
                "producto_id": p.producto_id,
                "codigo": p.codigo,
                "nombre": p.nombre,
                "precio": float(p.precio_venta),
                "stock": p.stock_actual
            })
        
        return {
            "success": True,
            "total": len(resultado),
            "productos": resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PRUEBA 3: INSERCIÓN (POST)
# ============================================
class ProductoTestCreate(BaseModel):
    codigo: str
    nombre: str
    precio: float
    stock: int

@router.post("/api/vfp/test/producto/crear")
async def test_crear_producto(
    producto: ProductoTestCreate,
    token_ok: bool = Depends(verificar_token_vfp),
    db: Session = Depends(get_db)
):
    """Crear un producto de prueba"""
    try:
        # Verificar si ya existe
        existe = db.query(ProductoModel).filter(
            ProductoModel.codigo == producto.codigo
        ).first()
        
        if existe:
            return {
                "success": False,
                "message": f"Producto {producto.codigo} ya existe",
                "producto_id": existe.producto_id
            }
        
        # Crear producto
        nuevo = ProductoModel(
            codigo=producto.codigo,
            nombre=producto.nombre,
            descripcion=f"Producto de prueba creado desde VFP",
            precio_venta=producto.precio,
            stock_actual=producto.stock,
            stock_minimo=0,
            categoria_id=1,  # Categoría por defecto
            unidad_medida_id=1,  # Unidad por defecto
            activo=True
        )
        
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        
        return {
            "success": True,
            "message": "Producto creado exitosamente",
            "producto_id": nuevo.producto_id,
            "codigo": nuevo.codigo
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PRUEBA 4: ACTUALIZACIÓN (PUT)
# ============================================
class ProductoTestUpdate(BaseModel):
    stock: int

@router.put("/api/vfp/test/producto/{codigo}/stock")
async def test_actualizar_stock(
    codigo: str,
    datos: ProductoTestUpdate,
    token_ok: bool = Depends(verificar_token_vfp),
    db: Session = Depends(get_db)
):
    """Actualizar stock de un producto"""
    try:
        producto = db.query(ProductoModel).filter(
            ProductoModel.codigo == codigo
        ).first()
        
        if not producto:
            return {
                "success": False,
                "message": f"Producto {codigo} no encontrado"
            }
        
        stock_anterior = producto.stock_actual
        producto.stock_actual = datos.stock
        
        db.commit()
        
        return {
            "success": True,
            "message": "Stock actualizado",
            "codigo": codigo,
            "stock_anterior": stock_anterior,
            "stock_nuevo": datos.stock
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))