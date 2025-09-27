# en api/endpoints/pedidos.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from core import auth # Asumo que tienes un archivo auth.py para las dependencias
from services import pedido_service

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Pedido,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo pedido",
    description="Crea un nuevo pedido con sus items, calcula los precios y totales desde el backend."
)
def create_pedido(
    *,
    db: Session = Depends(auth.get_db),
    pedido_in: schemas.PedidoCreate,
    current_vendedor: models.VendedorModel = Depends(auth.get_current_active_vendedor)
) -> models.PedidoModel:
    """
    Endpoint para la creación de un nuevo pedido.

    - **pedido_in**: Datos del pedido a crear, incluyendo la lista de items.
    - **current_vendedor**: Vendedor autenticado que realiza el pedido (obtenido del token).
    """
    try:
        nuevo_pedido = pedido_service.create_new_pedido(
            db=db, pedido_in=pedido_in, vendedor=current_vendedor
        )
        return nuevo_pedido
    except ValueError as e:
        # Errores de negocio (ej. stock, cliente inactivo) se capturan aquí
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Errores inesperados
        # En producción, aquí deberías loggear el error `e`
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al procesar el pedido.",
        )