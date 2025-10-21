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
        "message": "Conexión exitosa desde VFP - [by DuilioRestuccia]",
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
                "producto_id": p.id,
                "codigo": p.codigo_producto,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "precio_unitario": float(p.precio_unitario) if p.precio_unitario else 0.0,
                "precio_mayorista": float(p.precio_mayorista) if p.precio_mayorista else 0.0,
                "precio_distribuidor": float(p.precio_distribuidor) if p.precio_distribuidor else 0.0,
                "activo": p.activo
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
    precio_unitario: float
    precio_mayorista: Optional[float] = None
    precio_distribuidor: Optional[float] = None

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
            ProductoModel.codigo_producto == producto.codigo
        ).first()
        
        if existe:
            return {
                "success": False,
                "message": f"Producto {producto.codigo} ya existe",
                "producto_id": existe.id
            }
        
        # Crear producto
        nuevo = ProductoModel(
            codigo_producto=producto.codigo,
            nombre=producto.nombre,
            descripcion=f"Producto de prueba creado desde VFP  - [by DuilioRestuccia]",
            precio_unitario=producto.precio_unitario,
            precio_mayorista=producto.precio_mayorista,
            precio_distribuidor=producto.precio_distribuidor,
            categoria_id=1,  # Categoría por defecto
            activo=True
        )
        
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        
        return {
            "success": True,
            "message": "Producto creado exitosamente",
            "producto_id": nuevo.id,
            "codigo": nuevo.codigo_producto
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PRUEBA 4: ACTUALIZACIÓN (PUT)
# ============================================
class ProductoTestUpdate(BaseModel):
    precio_unitario: Optional[float] = None
    precio_mayorista: Optional[float] = None
    precio_distribuidor: Optional[float] = None

@router.put("/api/vfp/test/producto/{codigo}/precio")
async def test_actualizar_precio(
    codigo: str,
    datos: ProductoTestUpdate,
    token_ok: bool = Depends(verificar_token_vfp),
    db: Session = Depends(get_db)
):
    """Actualizar precios de un producto"""
    try:
        producto = db.query(ProductoModel).filter(
            ProductoModel.codigo_producto == codigo
        ).first()
        
        if not producto:
            return {
                "success": False,
                "message": f"Producto {codigo} no encontrado"
            }
        
        cambios = []
        
        if datos.precio_unitario is not None:
            producto.precio_unitario = datos.precio_unitario
            cambios.append(f"precio_unitario: {datos.precio_unitario}")
            
        if datos.precio_mayorista is not None:
            producto.precio_mayorista = datos.precio_mayorista
            cambios.append(f"precio_mayorista: {datos.precio_mayorista}")
            
        if datos.precio_distribuidor is not None:
            producto.precio_distribuidor = datos.precio_distribuidor
            cambios.append(f"precio_distribuidor: {datos.precio_distribuidor}")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Precios actualizados",
            "codigo": codigo,
            "cambios": cambios
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))