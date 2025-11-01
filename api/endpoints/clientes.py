from sqlalchemy import and_, or_
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database import get_db
from core.auth import get_current_user
from app.models.client_models import ClienteModel, TipoClienteModel
from crud.crud_client import crud_cliente

from app.schemas.client_schemas import (
    ClienteCreate,
    ClienteResponse,
    ClienteListResponse,
    ClienteUpdate,
    ClienteSelectResponse
)

from app.apis.utils import (api_client, validar_formato_ruc, validar_formato_dni, procesar_datos_empresa, procesar_datos_persona)

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

# ============================================================================
# ENDPOINTS PARA GESTIÓN DE CLIENTES
# ============================================================================

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def crear_nuevo_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Crear un nuevo cliente**
    
    Registra un nuevo cliente en el sistema con validación de RUC único.
    Si se proporcionan datos del titular (DNI y nombres), se crea automáticamente
    un contacto principal asociado.
    
    **Requiere autenticación de usuario**
    
    **Validaciones:**
    - RUC único (11 dígitos)
    - Teléfono válido (7-15 dígitos)
    - Email válido (opcional)
    - Tipo de cliente debe existir
    
    **Returns:**
    - Cliente creado con código generado automáticamente
    """
    try:
        db_cliente = crud_cliente.create_with_user(
            db, 
            obj_in=cliente, 
            usuario_id=current_user["user_id"]
        )
        return db_cliente
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear cliente: {str(e)}"
        )


@router.get("/", response_model=List[ClienteListResponse])
async def listar_clientes(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    tipo_cliente_id: Optional[int] = None,
    buscar: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Listar clientes con filtros**
    
    Obtiene una lista paginada de clientes con opciones de filtrado.
    
    **Parámetros de query:**
    - `skip`: Número de registros a saltar (default: 0)
    - `limit`: Límite de registros (default: 100)
    - `activo`: Filtrar por estado (true/false)
    - `tipo_cliente_id`: Filtrar por tipo de cliente
    - `buscar`: Búsqueda por nombre, razón social, RUC o código
    
    **Requiere autenticación**
    """
    clientes = crud_cliente.get_multi_filtered(
        db,
        skip=skip,
        limit=limit,
        activo=activo,
        tipo_cliente_id=tipo_cliente_id,
        buscar=buscar
    )
    return clientes


@router.get("/select", response_model=List[ClienteSelectResponse])
async def listar_clientes_select(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Lista simple de clientes para select/dropdown**
    
    Retorna solo clientes activos con información básica.
    Útil para poblar selects en formularios.
    
    **Requiere autenticación**
    """
    clientes = crud_cliente.get_activos_simple(db)
    return clientes


@router.get("/ruc/{ruc}", response_model=ClienteResponse)
async def obtener_cliente_por_ruc(
    ruc: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Buscar cliente por RUC**
    
    Útil para verificar si un cliente ya está registrado antes de crear uno nuevo.
    
    **Requiere autenticación**
    """
    db_cliente = crud_cliente.get_by_ruc(db, ruc=ruc)
    
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe cliente con RUC {ruc}"
        )
    
    return db_cliente



@router.put("/{cliente_id}", response_model=ClienteResponse)
async def actualizar_cliente(
    cliente_id: int,
    cliente_update: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Actualizar datos de cliente**
    
    Actualiza uno o más campos de un cliente existente.
    Solo se actualizan los campos proporcionados en el request.
    
    **Requiere autenticación**
    """
    db_cliente = crud_cliente.get(db, id=cliente_id)
    
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    db_cliente = crud_cliente.update(db, db_obj=db_cliente, obj_in=cliente_update)
    return db_cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Desactivar cliente (soft delete)**
    
    Marca el cliente como inactivo sin eliminarlo de la base de datos.
    
    **Requiere autenticación**
    """
    success = crud_cliente.desactivar(db, id=cliente_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return None


@router.post("/{cliente_id}/activar", response_model=ClienteResponse)
async def activar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Reactivar cliente desactivado**
    
    Marca el cliente como activo nuevamente.
    
    **Requiere autenticación**
    """
    success = crud_cliente.activar(db, id=cliente_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    db_cliente = crud_cliente.get(db, id=cliente_id)
    return db_cliente


# ============================================================================

# ========================================
# ✅ RUTAS ESPECÍFICAS (PRIMERO)
# ========================================

@router.get("/buscar")
async def buscar_clientes(
    q: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Buscar clientes por RUC, nombre comercial, razón social o teléfono"""
    
    try:
        clientes = db.query(ClienteModel).filter(
            ClienteModel.activo == True,
            or_(
                ClienteModel.ruc.ilike(f"%{q}%"),
                ClienteModel.nombre_comercial.ilike(f"%{q}%"),
                ClienteModel.razon_social.ilike(f"%{q}%"),
                ClienteModel.telefono.ilike(f"%{q}%")
            )
        ).limit(10).all()
        
        resultados = []
        for c in clientes:
            tipo_nombre = None
            if c.tipo_cliente_id:
                try:
                    tipo_cliente = db.query(TipoClienteModel).filter(
                        TipoClienteModel.id == c.tipo_cliente_id
                    ).first()
                    tipo_nombre = tipo_cliente.nombre if tipo_cliente else "Sin tipo"
                except Exception as e:
                    tipo_nombre = "Sin tipo"
            
            resultados.append({
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
                    "nombre": tipo_nombre or "Sin tipo"
                }
            })
        
        return {
            "success": True,
            "message": f"Encontrados {len(resultados)} clientes",
            "data": resultados
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")



@router.get("/validar-ruc/{ruc}")
async def validar_ruc_sunat(
    ruc: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Valida RUC consultando SUNAT vía apisperu.com"""
    
    if not validar_formato_ruc(ruc):
        raise HTTPException(400, "RUC debe tener 11 dígitos y empezar con 10 o 20")
    
    try:
        data = api_client.get_company(ruc)
        resultado = procesar_datos_empresa(data)
        
        es_persona_natural = ruc.startswith('10')
        
        return {
            "success": True,
            "ruc": ruc,
            "razon_social": resultado["razonSocial"],
            "nombre_comercial": resultado.get("nombreComercial", ""),  # ✅ NUEVO
            "direccion": resultado["direccion"],
            "distrito": resultado["distrito"],
            "provincia": resultado["provincia"],
            "departamento": resultado["departamento"],
            "estado": resultado["estado"],
            "condicion": resultado["condicion"],
            "es_persona_natural": es_persona_natural
        }
    except Exception as e:
        raise HTTPException(500, f"Error validando RUC: {str(e)}")
    


# ============================================================================

@router.get("/validar-dni/{dni}")
async def validar_dni_reniec(
    dni: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Valida DNI consultando RENIEC vía apisperu.com"""
    
    print(f"\n🔍 Validando DNI: {dni}")
    
    if not validar_formato_dni(dni):
        raise HTTPException(400, "DNI debe tener 8 dígitos")
    
    try:
        data = api_client.get_person(dni)
        print(f"📦 Respuesta API: {data}")
        
        # ✅ VERIFICAR SI LA API RETORNÓ ERROR
        if isinstance(data, dict) and data.get('success') == False:
            return {
                "success": False,
                "message": data.get('message', 'DNI no encontrado')
            }
        
        # ✅ VERIFICAR QUE TENGA DATOS
        if not data or not data.get('nombres'):
            return {
                "success": False,
                "message": "DNI no encontrado en RENIEC"
            }
        
        resultado = procesar_datos_persona(data)
        
        return {
            "success": True,
            "dni": dni,
            "nombres": resultado["nombres"],
            "apellido_paterno": resultado["apellidoPaterno"],
            "apellido_materno": resultado["apellidoMaterno"],
            "nombre_completo": resultado["nombreCompleto"]
        }
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        raise HTTPException(500, f"Error validando DNI: {str(e)}")
    


# ========================================
# ✅ RUTAS CON PARÁMETROS (AL FINAL)
# ========================================
@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    **Obtener cliente por ID**
    
    Retorna información completa de un cliente específico.
    
    **Requiere autenticación**
    """
    db_cliente = crud_cliente.get(db, id=cliente_id)
    
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    return db_cliente