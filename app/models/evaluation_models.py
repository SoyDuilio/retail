from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base
from .order_models import EstadoPedidoEnum, get_utc_now

class CalificacionModel(Base):
    __tablename__ = "calificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), unique=True)
    estado = Column(SQLEnum(EstadoPedidoEnum), default=EstadoPedidoEnum.PENDIENTE)
    observaciones = Column(Text)
    created_at = Column(DateTime, default=get_utc_now)
    
    # Relación
    pedido = relationship("PedidoModel", back_populates="calificacion")