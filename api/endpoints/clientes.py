print("=" * 50)
print("🔵 CLIENTES.PY SE ESTÁ IMPORTANDO")
print("=" * 50)

from fastapi import APIRouter, Depends, HTTPException, status
print("=" * 50)
print("🟢 CLIENTES.PY IMPORTADO CORRECTAMENTE")
print(f"Router prefix: {router.prefix if 'router' in locals() else 'NO DEFINIDO'}")
print("=" * 50)

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.database import get_db
from core.auth import get_current_user
from crud.crud_client import crud_cliente

from app.schemas.client_schemas import (
    ClienteCreate,
    ClienteResponse,
    ClienteListResponse,
    ClienteUpdate,
    ClienteSelectResponse
)

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])

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

