from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any

from app.database import get_db
from core.auth import get_current_user
from app.models.client_models import ClienteModel

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])


@router.get("/")
async def buscar_clientes(
    buscar: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Buscar clientes por RUC, nombre o razón social"""
    
    print(f"🔍 Buscando clientes con: '{buscar}'")
    
    try:
        clientes = db.query(ClienteModel).filter(
            ClienteModel.activo == True,
            or_(
                ClienteModel.ruc.ilike(f"%{buscar}%"),
                ClienteModel.nombre_comercial.ilike(f"%{buscar}%"),
                ClienteModel.razon_social.ilike(f"%{buscar}%")
            )
        ).limit(10).all()
        
        print(f"✅ Encontrados: {len(clientes)} clientes")
        
        return [
            {
                "id": c.id,
                "codigo_cliente": c.codigo_cliente,
                "nombre_comercial": c.nombre_comercial,
                "razon_social": c.razon_social,
                "ruc": c.ruc,
                "telefono": c.telefono,
                "distrito": c.distrito,
                "tipo_cliente_id": c.tipo_cliente_id,
                "tipo_cliente": {
                    "id": c.tipo_cliente_id,
                    "nombre": "Cliente"  # Simplificado por ahora
                }
            }
            for c in clientes
        ]
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
