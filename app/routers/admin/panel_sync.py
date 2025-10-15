from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
import csv
import io

from app.database import get_db
from app.models.order_models import PedidoModel
from app.models.product_models import ProductoModel
from app.models.client_models import ClienteModel

router = APIRouter(prefix="/admin/vfp-sync", tags=["admin-sync"])
templates = Jinja2Templates(directory="templates")

# Autenticación simple (cambiar por algo más robusto)
ADMIN_PASSWORD = "admin_vfp_2025"

def verify_admin(password: str):
    return password == ADMIN_PASSWORD

@router.get("", response_class=HTMLResponse)
async def panel_sync(request: Request, db: Session = Depends(get_db)):
    """Panel de sincronización VFP"""
    
    # Estadísticas
    total_productos = db.query(ProductoModel).count()
    total_clientes = db.query(ClienteModel).count()
    pedidos_pendientes = db.query(PedidoModel).filter(
        PedidoModel.estado.in_(["pendiente_aprobacion", "aprobado"])
    ).count()
    
    # Últimos 20 pedidos
    pedidos_recientes = db.query(PedidoModel).order_by(
        PedidoModel.fecha_creacion.desc()
    ).limit(20).all()
    
    return templates.TemplateResponse("admin/panel_sync.html", {
        "request": request,
        "total_productos": total_productos,
        "total_clientes": total_clientes,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_recientes": pedidos_recientes
    })

@router.get("/descargar-pedidos-csv")
async def descargar_pedidos_csv(db: Session = Depends(get_db)):
    """Descargar pedidos pendientes en CSV"""
    
    pedidos = db.query(PedidoModel).filter(
        PedidoModel.estado.in_(["pendiente_aprobacion", "aprobado"])
    ).order_by(PedidoModel.fecha_creacion.desc()).all()
    
    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "ID", "Numero_Pedido", "Fecha", "Hora", "Estado",
        "Vendedor_DNI", "Cliente_RUC", "Cliente_Nombre",
        "Tipo_Pago", "Total"
    ])
    
    # Datos
    for p in pedidos:
        writer.writerow([
            p.id,
            p.numero_pedido,
            p.fecha.isoformat() if p.fecha else "",
            p.hora.strftime("%H:%M:%S") if p.hora else "",
            p.estado,
            p.vendedor.dni if p.vendedor else "",
            p.cliente.ruc if p.cliente else "",
            p.cliente.nombre_comercial if p.cliente else "",
            p.tipo_pago if hasattr(p.tipo_pago, 'value') else str(p.tipo_pago),
            float(p.total)
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=pedidos_{date.today()}.csv"
        }
    )

@router.get("/descargar-productos-csv")
async def descargar_productos_csv(db: Session = Depends(get_db)):
    """Descargar productos en CSV"""
    
    productos = db.query(ProductoModel).filter(
        ProductoModel.activo == True
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "Codigo", "Nombre", "Precio_Base", "Stock_Actual", "Activo"])
    
    for p in productos:
        writer.writerow([
            p.id,
            p.codigo_producto,
            p.nombre,
            float(p.precio_base) if p.precio_base else 0,
            float(p.stock_actual) if p.stock_actual else 0,
            p.activo
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=productos_{date.today()}.csv"
        }
    )