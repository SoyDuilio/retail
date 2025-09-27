# en crud/crud_precio.py

from sqlalchemy.orm import Session
from .base import CRUDBase # Asumo que tienes una clase base para CRUD
from app import models

class CRUDPrecio(CRUDBase[models.PrecioModel, None, None]):
    def get_for_product_and_client_type(
        self, db: Session, *, producto_id: int, tipo_cliente_id: int
    ) -> models.PrecioModel | None:
        return db.query(self.model).filter(
            models.PrecioModel.producto_id == producto_id,
            models.PrecioModel.tipo_cliente_id == tipo_cliente_id
        ).first()

precio = CRUDPrecio(models.PrecioModel)