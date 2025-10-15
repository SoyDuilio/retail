from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.order_models import PedidoModel, PedidoItemModel
from app.models.product_models import ProductoModel
from app.models.client_models import ClienteModel

router = APIRouter(
    prefix="/api/vfp",
    tags=["vfp-sync"]
)

# ==================== AUTENTICACIÓN SIMPLE ====================
VFP_TOKEN = "VFP_SYNC_TOKEN_2025_DUILIO_STORE_SECURE"  # Cambiar por uno seguro

def verify_vfp_token(authorization: str = Header(None)):
    """Verificar token de VFP"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    if authorization != f"Bearer {VFP_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return True

# ==================== SCHEMAS ====================
class PedidoNuevoVFP(BaseModel):
    """Estructura simplificada de pedido para VFP"""
    numero_pedido: str
    fecha: str  # YYYY-MM-DD
    hora: str   # HH:MM:SS
    cliente_ruc: str
    vendedor_dni: str
    total: float
    items: List[dict]  # [{"codigo": "PROD-001", "cantidad": 10, "precio": 5.50}]

class ProductoVFP(BaseModel):
    """Estructura simplificada de producto"""
    codigo_producto: str
    nombre: str
    precio_base: float
    stock_actual: float
    activo: bool = True

# ==================== ENDPOINTS ====================

@router.get("/test")
async def test_conexion(token_ok: bool = Depends(verify_vfp_token)):
    """Endpoint de prueba para verificar conexión"""
    return {
        "success": True,
        "message": "Conexión exitosa con Railway",
        "timestamp": datetime.now().isoformat(),
        "server": "Railway PostgreSQL"
    }

# ==================== PEDIDOS ====================

@router.get("/pedidos/nuevos")
async def obtener_pedidos_nuevos(
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db)
):
    """Obtener pedidos pendientes desde la web (creados por vendedores externos)"""
    try:
        # Obtener pedidos pendientes de aprobación o aprobados que no se han procesado
        pedidos = db.query(PedidoModel).filter(
            PedidoModel.estado.in_(["pendiente_aprobacion", "aprobado"])
        ).order_by(PedidoModel.fecha_creacion.desc()).limit(100).all()
        
        resultado = []
        for p in pedidos:
            # Obtener items del pedido
            items = []
            for item in p.items:
                items.append({
                    "producto_codigo": item.producto.codigo_producto if item.producto else "",
                    "producto_nombre": item.producto.nombre if item.producto else "",
                    "cantidad": float(item.cantidad),
                    "precio_unitario": float(item.precio_unitario_venta),
                    "subtotal": float(item.subtotal)
                })
            
            resultado.append({
                "id": p.id,
                "numero_pedido": p.numero_pedido,
                "fecha": p.fecha.isoformat(),
                "hora": p.hora.strftime("%H:%M:%S"),
                "estado": p.estado,
                "vendedor_dni": p.vendedor.dni if p.vendedor else "",
                "vendedor_nombre": f"{p.vendedor.nombre} {p.vendedor.apellidos}" if p.vendedor else "",
                "cliente_ruc": p.cliente.ruc if p.cliente else "",
                "cliente_nombre": p.cliente.nombre_comercial if p.cliente else "",
                "tipo_pago": p.tipo_pago if hasattr(p.tipo_pago, 'value') else str(p.tipo_pago),
                "metodo_pago": p.metodo_pago,
                "total": float(p.total),
                "items_count": len(items),
                "items": items
            })
        
        return {
            "success": True,
            "count": len(resultado),
            "data": resultado
        }
        
    except Exception as e:
        print(f"Error obteniendo pedidos: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/pedidos/{pedido_id}/marcar-procesado")
async def marcar_pedido_procesado(
    pedido_id: int,
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db)
):
    """Marcar pedido como procesado en VFP"""
    try:
        pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
        
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Cambiar estado a "en_proceso" o "completado"
        pedido.estado = "en_proceso"
        db.commit()
        
        return {
            "success": True,
            "message": f"Pedido {pedido.numero_pedido} marcado como procesado",
            "pedido_id": pedido_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRODUCTOS ====================

@router.get("/productos")
async def listar_productos(
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db),
    limit: int = 1000
):
    """Listar todos los productos activos"""
    try:
        productos = db.query(ProductoModel).filter(
            ProductoModel.activo == True
        ).limit(limit).all()
        
        resultado = []
        for p in productos:
            resultado.append({
                "id": p.id,
                "codigo_producto": p.codigo_producto,
                "nombre": p.nombre,
                "precio_base": float(p.precio_base) if p.precio_base else 0,
                "stock_actual": float(p.stock_actual) if p.stock_actual else 0,
                "activo": p.activo
            })
        
        return {
            "success": True,
            "count": len(resultado),
            "data": resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productos/{codigo}")
async def buscar_producto(
    codigo: str,
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db)
):
    """Buscar producto por código"""
    try:
        producto = db.query(ProductoModel).filter(
            ProductoModel.codigo_producto == codigo
        ).first()
        
        if not producto:
            return {
                "success": False,
                "message": "Producto no encontrado"
            }
        
        return {
            "success": True,
            "data": {
                "id": producto.id,
                "codigo_producto": producto.codigo_producto,
                "nombre": producto.nombre,
                "precio_base": float(producto.precio_base) if producto.precio_base else 0,
                "stock_actual": float(producto.stock_actual) if producto.stock_actual else 0,
                "activo": producto.activo
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/productos/sync")
async def sincronizar_producto(
    producto: ProductoVFP,
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db)
):
    """Crear o actualizar producto desde VFP"""
    try:
        # Buscar si existe
        producto_existe = db.query(ProductoModel).filter(
            ProductoModel.codigo_producto == producto.codigo_producto
        ).first()
        
        if producto_existe:
            # Actualizar
            producto_existe.nombre = producto.nombre
            producto_existe.precio_base = producto.precio_base
            producto_existe.stock_actual = producto.stock_actual
            producto_existe.activo = producto.activo
            
            mensaje = f"Producto {producto.codigo_producto} actualizado"
        else:
            # Crear nuevo
            nuevo_producto = ProductoModel(
                codigo_producto=producto.codigo_producto,
                nombre=producto.nombre,
                precio_base=producto.precio_base,
                stock_actual=producto.stock_actual,
                activo=producto.activo
            )
            db.add(nuevo_producto)
            mensaje = f"Producto {producto.codigo_producto} creado"
        
        db.commit()
        
        return {
            "success": True,
            "message": mensaje,
            "codigo": producto.codigo_producto
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/productos/{codigo}/stock")
async def actualizar_stock(
    codigo: str,
    stock: float,
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db)
):
    """Actualizar solo el stock de un producto"""
    try:
        producto = db.query(ProductoModel).filter(
            ProductoModel.codigo_producto == codigo
        ).first()
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        producto.stock_actual = stock
        db.commit()
        
        return {
            "success": True,
            "message": f"Stock actualizado: {codigo} → {stock}",
            "codigo": codigo,
            "stock_nuevo": stock
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CLIENTES ====================

@router.get("/clientes")
async def listar_clientes(
    token_ok: bool = Depends(verify_vfp_token),
    db: Session = Depends(get_db),
    limit: int = 1000
):
    """Listar clientes activos"""
    try:
        clientes = db.query(ClienteModel).filter(
            ClienteModel.activo == True
        ).limit(limit).all()
        
        resultado = []
        for c in clientes:
            resultado.append({
                "id": c.id,
                "ruc": c.ruc,
                "razon_social": c.razon_social,
                "nombre_comercial": c.nombre_comercial,
                "direccion": c.direccion_completa,
                "telefono": c.telefono,
                "activo": c.activo
            })
        
        return {
            "success": True,
            "count": len(resultado),
            "data": resultado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))