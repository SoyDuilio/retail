"""
Modelos SQLAlchemy para configuración de precios
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class ConfiguracionDescuento(Base):
    """Configuración de descuentos por tipo de pago"""
    __tablename__ = "configuracion_descuentos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo_pago = Column(String(20), nullable=False, index=True)
    tipo_descuento = Column(String(20), nullable=False)
    valor_descuento = Column(Numeric(10, 2), nullable=False)
    aplica_sobre = Column(String(20), nullable=False, default="precio_base")
    descripcion = Column(Text)
    activo = Column(Boolean, default=True, index=True)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class ModificacionPedido(Base):
    """Registro de observaciones y modificaciones de pedidos"""
    __tablename__ = "modificaciones_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    evaluacion_id = Column(Integer)
    
    # Quién observó
    observado_por_id = Column(Integer, nullable=False)
    observado_por_tipo = Column(String(20), nullable=False)
    
    # Detalles
    tipo_modificacion = Column(String(30), nullable=False)
    items_afectados = Column(Text, nullable=False)  # JSON como string
    motivo_general = Column(Text, nullable=False)
    
    # Respuesta
    respuesta_vendedor = Column(String(30))
    respondido_en = Column(DateTime)
    comentario_vendedor = Column(Text)
    
    # Control
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    notificado_vendedor = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)