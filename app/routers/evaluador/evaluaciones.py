from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from core.auth import get_current_evaluador
from app.models.user_models import EvaluadorModel, VendedorModel
from app.models.order_models import PedidoModel, PedidoItemModel, EvaluacionPedidoModel
from app.models.client_models import ClienteModel
from app.schemas.common_schemas import DataResponse
from app.websocket_manager import notificar_pedido_aprobado, notificar_pedido_rechazado

router = APIRouter(
    prefix="/api/evaluador",
    tags=["evaluador"]
)

# ==================== SCHEMAS ====================

class EvaluarPedidoRequest(BaseModel):
    pedido_id: int
    resultado: str  # 'aprobado', 'rechazado'
    motivo_rechazo: Optional[str] = None
    observaciones: Optional[str] = None

# ==================== ENDPOINTS ====================

@router.get("/estadisticas")
async def estadisticas_evaluador(
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Estadísticas del evaluador para hoy"""
    try:
        hoy = date.today()
        
        # Pedidos pendientes de evaluación
        pendientes = db.query(PedidoModel).filter(
            PedidoModel.estado == "pendiente_aprobacion",
            PedidoModel.fecha == hoy
        ).count()
        
        # Evaluaciones hechas hoy
        evaluados_hoy = db.query(EvaluacionPedidoModel).filter(
            EvaluacionPedidoModel.evaluador_id == current_evaluador.evaluador_id,
            func.date(EvaluacionPedidoModel.fecha_evaluacion) == hoy
        ).count()
        
        # Tasa de aprobación
        aprobados = db.query(EvaluacionPedidoModel).filter(
            EvaluacionPedidoModel.evaluador_id == current_evaluador.evaluador_id,
            EvaluacionPedidoModel.resultado == "aprobado"
        ).count()
        
        total_evaluaciones = db.query(EvaluacionPedidoModel).filter(
            EvaluacionPedidoModel.evaluador_id == current_evaluador.evaluador_id
        ).count()
        
        tasa_aprobacion = (aprobados / total_evaluaciones * 100) if total_evaluaciones > 0 else 0
        
        return DataResponse(
            success=True,
            message="Estadísticas obtenidas",
            data={
                "pendientes": pendientes,
                "evaluados_hoy": evaluados_hoy,
                "tasa_aprobacion": round(tasa_aprobacion, 1)
            }
        )
        
    except Exception as e:
        print(f"Error en estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pedidos-pendientes")
async def pedidos_pendientes(
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Lista de pedidos pendientes de evaluación"""
    try:
        # Obtener pedidos pendientes
        pedidos = db.query(PedidoModel).filter(
            PedidoModel.estado == "pendiente_aprobacion"
        ).order_by(PedidoModel.fecha_creacion.desc()).all()
        
        resultado = []
        
        for pedido in pedidos:
            # Validaciones automáticas
            vendedor_activo = pedido.vendedor.activo if pedido.vendedor else False
            cliente_no_moroso = not pedido.cliente.es_moroso if pedido.cliente else True
            monto_dentro_limite = current_evaluador.puede_aprobar_monto(float(pedido.total))
            
            # Cliente en zona
            cliente_en_zona = True
            if current_evaluador.departamento_asignado and pedido.cliente:
                cliente_en_zona = current_evaluador.esta_en_zona(
                    pedido.cliente.departamento if pedido.cliente else None
                )
            
            # Calcular prioridad
            validaciones_ok = sum([
                vendedor_activo,
                cliente_no_moroso,
                monto_dentro_limite,
                cliente_en_zona
            ])
            
            prioridad = "normal"
            if validaciones_ok == 4:
                prioridad = "normal"
            elif validaciones_ok >= 2:
                prioridad = "urgente"
            else:
                prioridad = "critico"
            
            # ✅ CONVERTIR ENUMS A STRING
            tipo_venta_str = pedido.tipo_venta.value if hasattr(pedido.tipo_venta, 'value') else str(pedido.tipo_venta)
            tipo_pago_str = pedido.tipo_pago.value if hasattr(pedido.tipo_pago, 'value') else str(pedido.tipo_pago)
            
            resultado.append({
                "id": pedido.id,
                "numero_pedido": pedido.numero_pedido,
                "fecha": pedido.fecha.isoformat(),
                "hora": pedido.hora.strftime("%H:%M"),
                "vendedor_nombre": f"{pedido.vendedor.nombre} {pedido.vendedor.apellidos}" if pedido.vendedor else "N/D",
                "cliente_nombre": pedido.cliente.nombre_comercial if pedido.cliente else "N/D",
                "cliente_ruc": pedido.cliente.ruc if pedido.cliente else "",
                "total": float(pedido.total),
                "items_count": len(pedido.items) if pedido.items else 0,
                "tipo_pago": tipo_pago_str,  # ✅ Usar string convertido
                "prioridad": prioridad,
                
                # Validaciones
                "validaciones": {
                    "vendedor_activo": vendedor_activo,
                    "cliente_en_zona": cliente_en_zona,
                    "monto_dentro_limite": monto_dentro_limite,
                    "cliente_no_moroso": cliente_no_moroso
                }
            })
        
        return DataResponse(
            success=True,
            message=f"Se encontraron {len(resultado)} pedidos pendientes",
            data=resultado
        )
        
    except Exception as e:
        print(f"Error obteniendo pedidos pendientes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pedido/{pedido_id}")
async def detalle_pedido(
    pedido_id: int,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Detalle completo de un pedido para evaluación"""
    try:
        pedido = db.query(PedidoModel).filter(PedidoModel.id == pedido_id).first()
        
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Información del cliente
        cliente = pedido.cliente
        cliente_info = None
        
        if cliente:
            # Historial de pedidos del cliente
            pedidos_previos = db.query(PedidoModel).filter(
                PedidoModel.cliente_id == cliente.id,
                PedidoModel.id != pedido_id
            ).count()
            
            # Pedidos aprobados (en lugar de pagados)
            pedidos_aprobados = db.query(PedidoModel).filter(
                PedidoModel.cliente_id == cliente.id,
                PedidoModel.estado == "aprobado"
            ).count()

            tasa_pago = (pedidos_aprobados / pedidos_previos * 100) if pedidos_previos > 0 else 0
            
            cliente_info = {
                "id": cliente.id,
                "ruc": cliente.ruc,
                "razon_social": cliente.razon_social,
                "nombre_comercial": cliente.nombre_comercial,
                "direccion": cliente.direccion_completa,
                "departamento": cliente.departamento,
                "provincia": cliente.provincia,
                "distrito": cliente.distrito,
                "telefono": cliente.telefono,
                "es_moroso": cliente.es_moroso,
                "deuda_actual": float(cliente.deuda_actual) if cliente.deuda_actual else 0,
                "dias_mora": cliente.dias_mora if cliente.dias_mora else 0,
                "pedidos_previos": pedidos_previos,
                "tasa_pago": round(tasa_pago, 1)
            }
        
        # Items del pedido
        items = []
        for item in pedido.items:
            items.append({
                "producto_nombre": item.producto.nombre if item.producto else "N/D",
                "cantidad": float(item.cantidad),
                "precio_unitario": float(item.precio_unitario_venta),
                "subtotal": float(item.subtotal)
            })
        
        # Información del vendedor
        vendedor = pedido.vendedor
        vendedor_info = None
        
        if vendedor:
            vendedor_info = {
                "id": vendedor.vendedor_id,
                "nombre": f"{vendedor.nombre} {vendedor.apellidos}",
                "dni": vendedor.dni,
                "telefono": vendedor.telefono,
                "activo": vendedor.activo
            }
        
        return DataResponse(
            success=True,
            message="Detalle del pedido",
            data={
                "pedido": {
                    "id": pedido.id,
                    "numero_pedido": pedido.numero_pedido,
                    "fecha": pedido.fecha.isoformat(),
                    "hora": pedido.hora.strftime("%H:%M"),
                    "tipo_venta": pedido.tipo_venta,
                    "tipo_pago": pedido.tipo_pago,
                    "metodo_pago": pedido.metodo_pago,
                    "subtotal": float(pedido.subtotal),
                    "total": float(pedido.total),
                    "observaciones": pedido.observaciones,
                    "estado": pedido.estado
                },
                "items": items,
                "cliente": cliente_info,
                "vendedor": vendedor_info
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error obteniendo detalle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluar-pedido")
async def evaluar_pedido(
    evaluacion: EvaluarPedidoRequest,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Evaluar un pedido (aprobar o rechazar)"""
    try:
        # Verificar que el pedido existe
        pedido = db.query(PedidoModel).filter(PedidoModel.id == evaluacion.pedido_id).first()
        
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        if pedido.estado != "pendiente_aprobacion":
            raise HTTPException(status_code=400, detail="Este pedido ya fue evaluado")
        
        # Verificar si el evaluador puede aprobar el monto
        if evaluacion.resultado == "aprobado":
            if not current_evaluador.puede_aprobar_monto(float(pedido.total)):
                raise HTTPException(
                    status_code=403, 
                    detail=f"El monto S/ {pedido.total} excede tu límite de aprobación S/ {current_evaluador.limite_aprobacion}"
                )
        
        # Realizar validaciones automáticas
        vendedor_activo = pedido.vendedor.activo if pedido.vendedor else False
        cliente_no_moroso = not pedido.cliente.es_moroso if pedido.cliente else True
        monto_dentro_limite = current_evaluador.puede_aprobar_monto(float(pedido.total))
        
        cliente_en_zona = True
        if current_evaluador.departamento_asignado and pedido.cliente:
            cliente_en_zona = current_evaluador.esta_en_zona(pedido.cliente.departamento)
        
        # Crear registro de evaluación
        nueva_evaluacion = EvaluacionPedidoModel(
            pedido_id=evaluacion.pedido_id,
            evaluador_id=current_evaluador.evaluador_id,
            vendedor_activo=vendedor_activo,
            cliente_en_zona=cliente_en_zona,
            monto_dentro_limite=monto_dentro_limite,
            cliente_no_moroso=cliente_no_moroso,
            resultado=evaluacion.resultado,
            motivo_rechazo=evaluacion.motivo_rechazo,
            observaciones=evaluacion.observaciones,
            fecha_evaluacion=datetime.now()
        )
        
        db.add(nueva_evaluacion)
        
        # Actualizar estado del pedido
        if evaluacion.resultado == "aprobado":
            pedido.estado = "aprobado"
        else:
            pedido.estado = "rechazado"
        
        db.commit()
        
        # ✅ NOTIFICAR VÍA WEBSOCKET
        if evaluacion.resultado == "aprobado":
            await notificar_pedido_aprobado(
                pedido_id=str(pedido.numero_pedido),
                vendedor_id=pedido.vendedor_id,
                cliente_id=pedido.cliente_id,
                monto=float(pedido.total)
            )
        else:
            await notificar_pedido_rechazado(
                pedido_id=str(pedido.numero_pedido),
                vendedor_id=pedido.vendedor_id,
                cliente_id=pedido.cliente_id,
                motivo=evaluacion.motivo_rechazo or "No especificado"
            )
        
        return DataResponse(...)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historial-cliente/{cliente_id}")
async def historial_cliente(
    cliente_id: int,
    current_evaluador: EvaluadorModel = Depends(get_current_evaluador),
    db: Session = Depends(get_db)
):
    """Historial de pedidos de un cliente"""
    try:
        cliente = db.query(ClienteModel).filter(ClienteModel.id == cliente_id).first()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Últimos 10 pedidos
        pedidos = db.query(PedidoModel).filter(
            PedidoModel.cliente_id == cliente_id
        ).order_by(PedidoModel.fecha_creacion.desc()).limit(10).all()
        
        historial = []
        for p in pedidos:
            historial.append({
                "numero_pedido": p.numero_pedido,
                "fecha": p.fecha.isoformat(),
                "total": float(p.total),
                "estado": p.estado
            })
        
        return DataResponse(
            success=True,
            message="Historial del cliente",
            data=historial
        )
        
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))