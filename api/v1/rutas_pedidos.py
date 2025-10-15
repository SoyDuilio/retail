from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import uuid4

from app.database import get_db
from app.models.order_models import PedidoModel, PedidoItemModel
from app.models.product_models import ProductoModel
from app.models.user_models import VendedorModel
from app.models.client_models import ClienteModel
from core.auth import get_current_vendedor
from pydantic import BaseModel

from app.websocket_manager import notificar_pedido_nuevo

from sqlalchemy import text

# Schemas
class ItemPedidoCreate(BaseModel):
    producto_id: int
    cantidad: int
    override_tipo_cliente_id: int | None = None

class PedidoCreate(BaseModel):
    cliente_id: int
    tipo_venta: str
    tipo_pago: str
    latitud_pedido: float
    longitud_pedido: float
    observaciones: str | None = None
    items: List[ItemPedidoCreate]

router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])

@router.post("")
async def crear_pedido(
    pedido_data: PedidoCreate,
    db: Session = Depends(get_db),
    vendedor_actual: VendedorModel = Depends(get_current_vendedor)
):
    try:
        # Validar cliente
        cliente = db.query(ClienteModel).filter(
            ClienteModel.id == pedido_data.cliente_id,
            ClienteModel.activo == True
        ).first()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        if not pedido_data.items:
            raise HTTPException(status_code=400, detail="Debe agregar productos")
        
        # Crear pedido
        pedido_id = uuid4()
        ahora = datetime.now()
        count = db.query(PedidoModel).count()

        # Mapear modalidad de pago
        metodo_map = {
            "credito": "credito_15_dias",
            "efectivo_cash": "contado",
            "efectivo_yape": "yape_plin",
            "efectivo_plin": "yape_plin"
        }
        metodo_pago_value = metodo_map.get(pedido_data.tipo_pago, "contado")
        
        nuevo_pedido = PedidoModel(
            numero_pedido=f"PED-{count + 1:06d}",
            fecha=ahora.date(),
            hora=ahora.time(),
            cliente_id=pedido_data.cliente_id,
            vendedor_id=vendedor_actual.vendedor_id,
            tipo_venta=pedido_data.tipo_venta.upper(),  # ✅ EXTERNA
            tipo_pago=pedido_data.tipo_pago.upper(),    # ✅ CREDITO
            metodo_pago=metodo_pago_value,
            latitud_pedido=pedido_data.latitud_pedido,
            longitud_pedido=pedido_data.longitud_pedido,
            observaciones=pedido_data.observaciones,
            fecha_creacion=ahora,
            estado="pendiente_aprobacion"
        )

        db.add(nuevo_pedido)
        db.flush()  # ✅ Aquí se genera el ID automáticamente

        pedido_id = nuevo_pedido.id  # ✅ Ahora úsalo para los items
        
        subtotal = 0
        
        # Crear items
        for item in pedido_data.items:
            producto = db.query(ProductoModel).filter(
                ProductoModel.id == item.producto_id,
                ProductoModel.activo == True
            ).first()
            
            if not producto:
                raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")
            
            tipo_cliente_id = item.override_tipo_cliente_id or cliente.tipo_cliente_id
            
            precio_query = db.execute(
                text("SELECT precio FROM precios WHERE producto_id = :pid AND tipo_cliente_id = :tid"),
                {"pid": item.producto_id, "tid": tipo_cliente_id}
            ).first()
            
            if not precio_query:
                raise HTTPException(status_code=400, detail=f"Sin precio para {producto.nombre}")
            
            precio_unitario = float(precio_query[0])
            item_subtotal = precio_unitario * item.cantidad
            
            pedido_item = PedidoItemModel(
                pedido_id=nuevo_pedido.id,
                producto_id=item.producto_id,
                unidad_medida_venta="UND",
                cantidad=item.cantidad,
                precio_unitario_venta=precio_unitario,
                #descuento_aplicado=0,
                subtotal=item_subtotal,
                #total=item_subtotal
            )
            
            db.add(pedido_item)
            subtotal += item_subtotal
        
        nuevo_pedido.subtotal = subtotal
        nuevo_pedido.descuento_total = 0
        nuevo_pedido.total = subtotal
        nuevo_pedido.monto_total = subtotal
        
        db.commit()
        db.refresh(nuevo_pedido)

        # ✅ NOTIFICAR A EVALUADORES
        await notificar_pedido_nuevo({
            "id": nuevo_pedido.id,
            "numero_pedido": nuevo_pedido.numero_pedido,
            "vendedor_nombre": f"{vendedor_actual.nombre} {vendedor_actual.apellidos}",
            "cliente_nombre": cliente.nombre_comercial,
            "total": float(nuevo_pedido.total)
        })
        
        return {
            "success": True,
            "message": "Pedido creado",
            "data": {
                "pedido_id": str(nuevo_pedido.id),
                "numero_pedido": nuevo_pedido.numero_pedido,
                "total": float(nuevo_pedido.total),
                "estado": nuevo_pedido.estado
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))