from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date
from typing import List, Dict, Any

from app.database import get_db
from core.auth import get_current_vendedor
from app.models.user_models import VendedorModel
from app.models.order_models import PedidoModel, PedidoItemModel
from app.models.product_models import ProductoModel
from app.schemas.common_schemas import DataResponse

router = APIRouter(
    prefix="/api/vendedor/estadisticas",
    tags=["vendedor-estadisticas"]
)


@router.get("/hoy")
async def estadisticas_hoy(
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Estadísticas del vendedor para el día actual"""
    try:
        hoy = date.today()
        
        pedidos_hoy = db.query(PedidoModel).filter(
            PedidoModel.vendedor_id == current_vendedor.vendedor_id,
            PedidoModel.fecha == hoy
        ).all()
        
        total_pedidos = len(pedidos_hoy)
        total_ventas = sum(float(p.total) for p in pedidos_hoy)
        
        pendientes = sum(1 for p in pedidos_hoy if p.estado == "pendiente_aprobacion")
        aprobados = sum(1 for p in pedidos_hoy if p.estado == "aprobado")
        rechazados = sum(1 for p in pedidos_hoy if p.estado == "rechazado")
        
        return DataResponse(
            success=True,
            message="Estadísticas obtenidas",
            data={
                "pedidos": total_pedidos,
                "ventas": total_ventas,
                "pendientes": pendientes,
                "aprobados": aprobados,
                "rechazados": rechazados
            }
        )
    except Exception as e:
        print(f"Error en estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pedidos-hoy")
async def pedidos_hoy(
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Lista de pedidos del día"""
    try:
        hoy = date.today()
        
        pedidos = db.query(PedidoModel).filter(
            PedidoModel.vendedor_id == current_vendedor.vendedor_id,
            PedidoModel.fecha == hoy
        ).order_by(PedidoModel.fecha_creacion.desc()).all()  # ✅ CORREGIDO
        
        resultado = []
        for p in pedidos:
            resultado.append({
                "numero_pedido": p.numero_pedido,
                "hora": p.hora.strftime("%H:%M") if p.hora else "",
                "cliente_nombre": p.cliente.nombre_comercial if p.cliente else "N/D",
                "total": float(p.total),
                "estado": p.estado,
                "items_count": len(p.items) if p.items else 0
            })
        
        return DataResponse(
            success=True,
            message=f"Se encontraron {len(resultado)} pedidos",
            data=resultado
        )
    except Exception as e:
        print(f"Error obteniendo pedidos: {str(e)}")
        import traceback
        traceback.print_exc()  # ✅ AGREGADO para ver el error completo
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranking")
async def ranking_vendedores(
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Ranking de vendedores del día"""
    try:
        hoy = date.today()
        
        ranking = db.query(
            VendedorModel.vendedor_id,
            VendedorModel.nombre,
            VendedorModel.apellidos,
            func.count(PedidoModel.id).label('pedidos'),
            func.sum(PedidoModel.total).label('total_ventas')
        ).join(
            PedidoModel, VendedorModel.vendedor_id == PedidoModel.vendedor_id
        ).filter(
            PedidoModel.fecha == hoy,
            VendedorModel.activo == True
        ).group_by(
            VendedorModel.vendedor_id,
            VendedorModel.nombre,
            VendedorModel.apellidos
        ).order_by(
            desc('total_ventas')
        ).all()
        
        resultado = []
        posicion_actual = 0
        
        for idx, r in enumerate(ranking, 1):
            es_vendedor_actual = r.vendedor_id == current_vendedor.vendedor_id
            if es_vendedor_actual:
                posicion_actual = idx
            
            resultado.append({
                "posicion": idx,
                "vendedor_id": r.vendedor_id,
                "nombre": f"{r.nombre} {r.apellidos}",
                "pedidos": r.pedidos,
                "ventas": float(r.total_ventas or 0),
                "es_actual": es_vendedor_actual
            })
        
        return DataResponse(
            success=True,
            message="Ranking obtenido",
            data={
                "ranking": resultado,
                "mi_posicion": posicion_actual,
                "total_vendedores": len(resultado)
            }
        )
    except Exception as e:
        print(f"Error en ranking: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productos-top")
async def productos_mas_vendidos(
    current_vendedor: VendedorModel = Depends(get_current_vendedor),
    db: Session = Depends(get_db)
):
    """Top 10 productos más vendidos del vendedor"""
    try:
        hoy = date.today()
        
        top_productos = db.query(
            ProductoModel.nombre,
            ProductoModel.codigo_producto,
            func.sum(PedidoItemModel.cantidad).label('cantidad_total'),
            func.sum(PedidoItemModel.subtotal).label('ventas_total')  # ✅ CORREGIDO: usar subtotal en lugar de total
        ).join(
            PedidoItemModel, ProductoModel.id == PedidoItemModel.producto_id
        ).join(
            PedidoModel, PedidoItemModel.pedido_id == PedidoModel.id
        ).filter(
            PedidoModel.vendedor_id == current_vendedor.vendedor_id,
            PedidoModel.fecha == hoy
        ).group_by(
            ProductoModel.id,
            ProductoModel.nombre,
            ProductoModel.codigo_producto
        ).order_by(
            desc('cantidad_total')
        ).limit(10).all()
        
        resultado = []
        for p in top_productos:
            resultado.append({
                "nombre": p.nombre,
                "codigo": p.codigo_producto,
                "cantidad": int(p.cantidad_total),
                "ventas": float(p.ventas_total or 0)  # ✅ AGREGADO: protección contra NULL
            })
        
        return DataResponse(
            success=True,
            message=f"Top {len(resultado)} productos",
            data=resultado
        )
    except Exception as e:
        print(f"Error obteniendo productos top: {str(e)}")
        import traceback
        traceback.print_exc()  # ✅ AGREGADO
        raise HTTPException(status_code=500, detail=str(e))