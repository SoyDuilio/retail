"""
Router para cálculo de precios
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database import get_db
from services.pricing_service import PricingService
from app.schemas.order_schemas import (
    CalculoPrecioRequest,
    CalculoPrecioResponse,
    ComparacionPreciosRequest,
    ComparacionPreciosResponse,
    PrecioDetalle
)
# ✅ Importar clase y modelo
from crud.crud_client import CRUDCliente
from app.models.client_models import ClienteModel

router = APIRouter(prefix="/precios", tags=["precios"])

# ✅ Instanciar CRUD
crud_cliente = CRUDCliente(ClienteModel)


@router.post("/calcular", response_model=CalculoPrecioResponse)
def calcular_precio_producto(
    request: CalculoPrecioRequest,
    db: Session = Depends(get_db)
):
    """Calcula el precio de un producto"""
    
    pricing_service = PricingService(db)
    
    precio_info = pricing_service.obtener_precio_producto(
        producto_id=request.producto_id,
        tipo_cliente_id=request.tipo_cliente_id,
        tipo_pago=request.tipo_pago.lower(),
        cantidad=request.cantidad
    )
    
    if not precio_info:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró precio para producto {request.producto_id}"
        )
    
    return CalculoPrecioResponse(
        producto_id=request.producto_id,
        tipo_cliente_id=request.tipo_cliente_id,
        tipo_pago=request.tipo_pago,
        cantidad=request.cantidad,
        precio_info=PrecioDetalle(**precio_info)
    )


@router.post("/comparar", response_model=ComparacionPreciosResponse)
def comparar_precios_contado_credito(
    request: ComparacionPreciosRequest,
    db: Session = Depends(get_db)
):
    """Compara precios CONTADO vs CRÉDITO"""
    
    cliente = crud_cliente.get(db, id=request.cliente_id)
    if not cliente or not cliente.activo:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if not cliente.tipo_cliente_id:
        raise HTTPException(status_code=400, detail="Cliente sin tipo asignado")
    
    pricing_service = PricingService(db)
    
    items_comparacion = []
    total_credito = Decimal('0.00')
    total_contado = Decimal('0.00')
    
    for item in request.items:  # ✅ Ahora es ItemComparacion, no dict
        precios = pricing_service.calcular_ambos_precios(
            producto_id=item.producto_id,  # ✅ Acceso directo al atributo
            tipo_cliente_id=cliente.tipo_cliente_id,
            cantidad=item.cantidad  # ✅ Acceso directo al atributo
        )
        
        if not precios:
            continue
        
        items_comparacion.append({
            'producto_id': item.producto_id,
            'cantidad': item.cantidad,
            'precio_credito': precios['precio_credito'],
            'precio_contado': precios['precio_contado'],
            'ahorro': precios['ahorro_contado']
        })
        
        total_credito += precios['precio_credito']['subtotal']
        total_contado += precios['precio_contado']['subtotal']
    
    ahorro = total_credito - total_contado
    porcentaje = (ahorro / total_credito * 100) if total_credito > 0 else Decimal('0.00')
    
    return ComparacionPreciosResponse(
        items=items_comparacion,
        total_credito=total_credito,
        total_contado=total_contado,
        ahorro_contado=ahorro,
        porcentaje_ahorro=round(porcentaje, 2)
    )