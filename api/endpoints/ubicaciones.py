from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text
from typing import Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.database import get_db
from core.auth import get_current_user
from app.models.ubicacion_models import UbicacionVendedorModel
from app.models.user_models import VendedorModel
from pydantic import BaseModel 

router = APIRouter()

# ✅ AGREGAR: Schema para validar request
# ✅ Schema
class UbicacionRequest(BaseModel):
    latitud: float
    longitud: float
    precision_gps: Optional[float] = None
    tipo_registro: str = "automatico"
    cliente_id: Optional[int] = None
    pedido_id: Optional[int] = None
    bateria_porcentaje: Optional[int] = None
    conectividad: Optional[str] = None


# ========================================
# GUARDAR UBICACIÓN
# ========================================

# ✅ MODIFICAR: Endpoint para usar Body en lugar de Query params
@router.post("/api/ubicaciones/registrar")
async def registrar_ubicacion(
    ubicacion: UbicacionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra ubicación del vendedor"""
    
    try:
        print(f"📍 Recibiendo ubicación de vendedor {current_user['user_id']}")
        print(f"   Datos: lat={ubicacion.latitud}, lon={ubicacion.longitud}, precision={ubicacion.precision_gps}")
        
        if current_user["tipo_usuario"] != "vendedor":
            raise HTTPException(status_code=403, detail="Solo vendedores")
        
        # Crear registro
        nueva_ubicacion = UbicacionVendedorModel(
            vendedor_id=current_user["user_id"],
            latitud=Decimal(str(ubicacion.latitud)),
            longitud=Decimal(str(ubicacion.longitud)),
            precision_gps=Decimal(str(ubicacion.precision_gps)) if ubicacion.precision_gps else None,
            tipo_registro=ubicacion.tipo_registro,
            cliente_id=ubicacion.cliente_id,
            pedido_id=ubicacion.pedido_id,
            bateria_porcentaje=ubicacion.bateria_porcentaje,
            conectividad=ubicacion.conectividad
        )
        
        db.add(nueva_ubicacion)
        
        # Actualizar vendedor
        vendedor = db.query(VendedorModel).filter(
            VendedorModel.vendedor_id == current_user["user_id"]
        ).first()
        
        if vendedor:
            vendedor.latitud_actual = ubicacion.latitud
            vendedor.longitud_actual = ubicacion.longitud
            vendedor.precision_gps = ubicacion.precision_gps
            vendedor.ultima_ubicacion = datetime.now()
        
        db.commit()
        db.refresh(nueva_ubicacion)
        
        print(f"✅ Ubicación guardada: ID={nueva_ubicacion.id}")
        
        return {
            "success": True,
            "message": "Ubicación registrada",
            "data": {
                "id": nueva_ubicacion.id,
                "timestamp": nueva_ubicacion.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR guardando ubicación: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ========================================
# ÚLTIMAS UBICACIONES (MAPA EN TIEMPO REAL)
# ========================================

@router.get("/api/ubicaciones/ultimas")
async def obtener_ultimas_ubicaciones(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las últimas ubicaciones de todos los vendedores activos"""
    
    try:
        # ✅ Permitir supervisor, CEO Y vendedores (para testing)
        if current_user["tipo_usuario"] not in ["supervisor", "ceo", "vendedor"]:
            raise HTTPException(status_code=403, detail="No autorizado")
        
        # Si es vendedor, solo mostrar su propia ubicación
        where_clause = ""
        if current_user["tipo_usuario"] == "vendedor":
            where_clause = f"AND v.vendedor_id = {current_user['user_id']}"
        
        # Consulta SQL directa
        query = text(f"""
            SELECT DISTINCT ON (v.vendedor_id) 
                v.vendedor_id,
                v.codigo_vendedor,
                v.nombre,
                v.apellidos,
                v.dni,
                v.telefono,
                v.activo,
                uv.latitud,
                uv.longitud,
                uv.precision_gps,
                uv.timestamp,
                uv.tipo_registro,
                uv.bateria_porcentaje,
                uv.conectividad,
                EXTRACT(EPOCH FROM (NOW() - uv.timestamp))/60 AS minutos_desde_ultima_actualizacion
            FROM vendedores v
            LEFT JOIN ubicaciones_vendedor uv ON v.vendedor_id = uv.vendedor_id
            WHERE v.activo = TRUE {where_clause}
            ORDER BY v.vendedor_id, uv.timestamp DESC NULLS LAST
        """)
        
        result = db.execute(query)
        ubicaciones = []
        
        for row in result:
            ubicaciones.append({
                "vendedor_id": row.vendedor_id,
                "codigo_vendedor": row.codigo_vendedor,
                "nombre": row.nombre,
                "apellidos": row.apellidos,
                "dni": row.dni,
                "telefono": row.telefono,
                "activo": row.activo,
                "latitud": float(row.latitud) if row.latitud else None,
                "longitud": float(row.longitud) if row.longitud else None,
                "precision_gps": float(row.precision_gps) if row.precision_gps else None,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "tipo_registro": row.tipo_registro,
                "bateria_porcentaje": row.bateria_porcentaje,
                "conectividad": row.conectividad,
                "minutos_inactivo": round(row.minutos_desde_ultima_actualizacion) if row.minutos_desde_ultima_actualizacion else None
            })
        
        return {
            "success": True,
            "data": ubicaciones
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en ultimas ubicaciones: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ========================================
# HISTORIAL DE RUTA DE UN VENDEDOR
# ========================================

@router.get("/api/ubicaciones/historial/{vendedor_id}")
async def obtener_historial_ruta(
    vendedor_id: int,
    fecha: Optional[date] = Query(default=None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Historial de ubicaciones de un vendedor en una fecha específica"""
    
    try:
        if current_user["tipo_usuario"] == "vendedor" and current_user["user_id"] != vendedor_id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tu propio historial")
        
        if fecha is None:
            fecha = date.today()
        
        ubicaciones = db.query(UbicacionVendedorModel).filter(
            and_(
                UbicacionVendedorModel.vendedor_id == vendedor_id,
                func.date(UbicacionVendedorModel.timestamp) == fecha
            )
        ).order_by(UbicacionVendedorModel.timestamp).all()
        
        distancia_km = db.execute(
            text("SELECT calcular_distancia_recorrida(:vendedor_id, :fecha)"),
            {"vendedor_id": vendedor_id, "fecha": fecha}
        ).scalar()
        
        return {
            "success": True,
            "data": {
                "vendedor_id": vendedor_id,
                "fecha": fecha.isoformat(),
                "total_registros": len(ubicaciones),
                "distancia_recorrida_km": float(distancia_km) if distancia_km else 0,
                "ruta": [
                    {
                        "latitud": float(ub.latitud),
                        "longitud": float(ub.longitud),
                        "timestamp": ub.timestamp.isoformat(),
                        "tipo_registro": ub.tipo_registro,
                        "precision_gps": float(ub.precision_gps) if ub.precision_gps else None
                    }
                    for ub in ubicaciones
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")