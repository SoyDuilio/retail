from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.database import get_db
from app.models.client_models import ClienteModel
from app.models.order_models import PedidoModel
from core.auth import get_current_vendedor

router = APIRouter(prefix="/clientes", tags=["credito-clientes"])


@router.get("/{cliente_id}/credito")
async def obtener_info_credito(
    cliente_id: int,
    db: Session = Depends(get_db),
    vendedor_actual = Depends(get_current_vendedor)
):
    """Obtiene información crediticia completa del cliente"""
    
    print(f"🔍 Endpoint credito llamado - Cliente: {cliente_id}, Vendedor: {vendedor_actual.vendedor_id}")
    
    # Obtener cliente
    cliente = db.query(ClienteModel).filter(
        ClienteModel.id == cliente_id,
        ClienteModel.activo == True
    ).first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # ✅ Usar campos del CLIENTE directamente
    limite_credito = cliente.limite_credito if hasattr(cliente, 'limite_credito') and cliente.limite_credito else Decimal('5000.00')
    deuda_actual = cliente.deuda_actual if hasattr(cliente, 'deuda_actual') and cliente.deuda_actual else Decimal('0.00')
    dias_mora = cliente.dias_mora if hasattr(cliente, 'dias_mora') and cliente.dias_mora else 0
    es_moroso = cliente.es_moroso if hasattr(cliente, 'es_moroso') else False
    
    print(f"📊 Datos cliente: límite={limite_credito}, deuda={deuda_actual}, mora={dias_mora}")
    
    # Calcular crédito en uso (pedidos pendientes)
    credito_usado = db.query(func.sum(PedidoModel.total)).filter(
        PedidoModel.cliente_id == cliente_id,
        PedidoModel.tipo_pago == "CREDITO",
        PedidoModel.estado.in_(["aprobado", "en_proceso", "entregado"])
    ).scalar() or Decimal('0.00')
    
    print(f"💳 Crédito usado: {credito_usado}")
    
    # Crédito disponible
    credito_disponible = limite_credito - credito_usado - deuda_actual
    
    # Determinar estado
    if es_moroso and dias_mora > 30:
        estado = "bloqueado"
        puede_credito = False
        mensaje = f"Cliente bloqueado - {dias_mora} días de mora"
    elif es_moroso or deuda_actual > 0:
        estado = "moroso"
        puede_credito = dias_mora <= 15
        mensaje = f"Cliente moroso - Deuda: S/ {float(deuda_actual):.2f}"
    elif credito_disponible < (limite_credito * Decimal('0.20')):
        estado = "advertencia"
        puede_credito = True
        mensaje = "Crédito bajo - Considere pago al contado"
    else:
        estado = "normal"
        puede_credito = True
        mensaje = "Cliente al día"
    
    porcentaje_usado = 0
    if limite_credito > 0:
        porcentaje_usado = round(float((credito_usado / limite_credito) * 100), 2)
    
    resultado = {
        "cliente_id": cliente_id,
        "cliente_nombre": cliente.nombre_comercial or cliente.razon_social,
        "cliente_ruc": cliente.ruc,
        "limite_credito": float(limite_credito),
        "credito_usado": float(credito_usado),
        "credito_disponible": float(credito_disponible),
        "deuda_actual": float(deuda_actual),
        "dias_mora": dias_mora,
        "dias_credito_maximo": 30,
        "es_moroso": es_moroso,
        "estado": estado,
        "puede_credito": puede_credito,
        "mensaje": mensaje,
        "porcentaje_usado": porcentaje_usado,
        "ultima_fecha_pago": str(cliente.ultima_fecha_pago) if hasattr(cliente, 'ultima_fecha_pago') and cliente.ultima_fecha_pago else None
    }
    
    print(f"✅ Respuesta: {resultado}")
    return resultado