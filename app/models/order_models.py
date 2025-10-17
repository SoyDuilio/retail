# app/models/order_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Date, Time, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date, time, timezone
import uuid
import enum

from .base import Base

# Función auxiliar para obtener la hora actual en UTC
def get_utc_now():
    return datetime.now(timezone.utc)

# =============================================
# ENUMS PARA SQLALCHEMY
# =============================================

class EstadoPedidoEnum(enum.Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    PARCIAL = "parcial"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

class TipoVentaEnum(enum.Enum):
    EXTERNA = "externa"
    INTERNA = "interna"

class TipoPagoEnum(enum.Enum):
    CREDITO = "credito"
    CONTADO = "contado"
    YAPE = "yape"
    PLIN = "plin"

# =============================================
# PEDIDOS PRINCIPALES
# =============================================

class PedidoModel(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    numero_pedido = Column(String(20), unique=True, nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False)
    vendedor_id = Column(Integer, ForeignKey("vendedores.vendedor_id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    tipo_venta = Column(SQLEnum(TipoVentaEnum), nullable=False, index=True)
    tipo_pago = Column(SQLEnum(TipoPagoEnum), default=TipoPagoEnum.CREDITO, index=True)
    metodo_pago = Column(String(50), nullable=False, default='credito')
    latitud_pedido = Column(DECIMAL(10, 8))
    longitud_pedido = Column(DECIMAL(11, 8))
    subtotal = Column(DECIMAL(12, 2), default=0)
    descuento_total = Column(DECIMAL(12, 2), default=0)
    total = Column(DECIMAL(12, 2), default=0, index=True)
    monto_total = Column(DECIMAL(12, 2), nullable=False, default=0)
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime(timezone=True), default=get_utc_now, index=True)
    #fecha_actualizacion = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    # Relaciones
    vendedor = relationship("VendedorModel", back_populates="pedidos")
    cliente = relationship("ClienteModel", back_populates="pedidos")
    items = relationship("PedidoItemModel", back_populates="pedido", cascade="all, delete-orphan")
    calificacion = relationship("CalificacionModel", back_populates="pedido", uselist=False, cascade="all, delete-orphan")    
    auditoria = relationship("AuditoriaPedidoModel", back_populates="pedido")
    estado = Column(String(20), default="pendiente", index=True)
    evaluacion = relationship("EvaluacionPedidoModel", back_populates="pedido", uselist=False)
    
    #@property
    #def estado(self):
    #    """Estado actual del pedido"""
    #    if self.calificacion:
    #        return self.calificacion.estado.value
    #    return "pendiente"
    
    @property
    def tiempo_transcurrido(self):
        """Tiempo transcurrido desde la creación"""
        delta = get_utc_now() - self.created_at
        
        if delta.days > 0:
            return f"{delta.days}d {delta.seconds // 3600}h"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
        else:
            return f"{delta.seconds // 60}m"
    
    @property
    def minutos_transcurridos(self):
        """Minutos transcurridos desde la creación"""
        delta = get_utc_now() - self.created_at
        return delta.days * 24 * 60 + delta.seconds // 60
    
    @property
    def prioridad(self):
        """Calcular prioridad del pedido"""
        minutos = self.minutos_transcurridos
        
        if minutos > 30 or float(self.total) > 1000:
            return "alta"
        elif minutos > 15 or float(self.total) > 500:
            return "media"
        else:
            return "baja"
    
    @property
    def requiere_credito(self):
        """¿El pedido requiere evaluación crediticia?"""
        return self.tipo_pago == TipoPagoEnum.CREDITO
    
    @property
    def items_resumen(self):
        """Resumen de items del pedido"""
        if not self.items:
            return "Sin items"
        
        if len(self.items) == 1:
            item = self.items[0]
            return f"{item.cantidad}x {item.producto.nombre if item.producto else 'Producto'}"
        else:
            return f"{len(self.items)} productos diferentes"
    
    def calcular_totales(self):
        """Recalcular totales del pedido"""
        if not self.items:
            self.subtotal = self.descuento_total = self.total = 0
            return
        
        subtotal = sum(float(item.subtotal) for item in self.items)
        descuento_total = sum(float(item.subtotal) - float(item.total) for item in self.items)
        total = sum(float(item.total) for item in self.items)
        
        self.subtotal = subtotal
        self.descuento_total = descuento_total
        self.total = total
        self.updated_at = get_utc_now()
    
    def puede_ser_evaluado(self):
        """¿El pedido puede ser evaluado?"""
        return (not self.calificacion or 
                self.calificacion.estado == EstadoPedidoEnum.PENDIENTE)
    
    def __repr__(self):
        return f"<Pedido {self.numero_pedido} - {self.cliente.nombre_completo if self.cliente else 'N/A'}: ${self.total}>"

# =============================================
# ITEMS DE PEDIDOS
# =============================================

class PedidoItemModel(Base):
    __tablename__ = "pedido_items"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    unidad_medida_venta = Column(String(50), nullable=False, default="UND")
    cantidad = Column(Integer, nullable=False)
    precio_unitario_venta = Column(DECIMAL(10, 2), nullable=False)
    #descuento_aplicado = Column(DECIMAL(5, 2), default=0)  # Porcentaje
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    #total = Column(DECIMAL(12, 2), nullable=False)
    #created_at = Column(DateTime, default=get_utc_now)
    
    # Relaciones
    pedido = relationship("PedidoModel", back_populates="items")
    producto = relationship("ProductoModel", back_populates="items_pedido")
    
    @property
    def descuento_monto(self):
        """Monto del descuento aplicado"""
        return float(self.subtotal) - float(self.total)
    
    @property
    def precio_final_unitario(self):
        """Precio final por unidad después del descuento"""
        return float(self.total) / self.cantidad if self.cantidad > 0 else 0
    
    @property
    def tiene_descuento(self):
        """¿Tiene descuento aplicado?"""
        return self.descuento_aplicado > 0
    
    def calcular_totales(self):
        """Calcular subtotal y total del item"""
        self.subtotal = float(self.precio_unitario) * self.cantidad
        
        if self.descuento_aplicado > 0:
            descuento_monto = self.subtotal * (float(self.descuento_aplicado) / 100)
            self.total = self.subtotal - descuento_monto
        else:
            self.total = self.subtotal
    
    def __repr__(self):
        return f"<PedidoItem {self.cantidad}x {self.producto.nombre if self.producto else 'Producto'} = ${self.total}>"

# =============================================
# CALIFICACIONES/EVALUACIONES
# =============================================



# =============================================
# AUDITORIA DE PEDIDOS
# =============================================

class AuditoriaPedidoModel(Base):
    __tablename__ = "auditoria_pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"))
    accion = Column(String(50), nullable=False, index=True)
    usuario_id = Column(Integer, nullable=False)
    usuario_tipo = Column(String(20), nullable=False)
    valores_anteriores = Column(Text)
    valores_nuevos = Column(Text)
    timestamp = Column(DateTime, default=get_utc_now, index=True)
    
    # Agregar esta línea:
    pedido = relationship("PedidoModel", back_populates="auditoria")

#   valores_

class EvaluacionPedidoModel(Base):
    __tablename__ = "evaluaciones_pedido"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    evaluador_id = Column(Integer, ForeignKey("evaluadores.evaluador_id"), nullable=False)
    
    # Validaciones automáticas
    vendedor_activo = Column(Boolean)
    cliente_en_zona = Column(Boolean)
    monto_dentro_limite = Column(Boolean)
    cliente_no_moroso = Column(Boolean)
    
    # Resultado
    resultado = Column(String(20), nullable=False)  # 'aprobado', 'rechazado', 'pendiente'
    motivo_rechazo = Column(Text)
    observaciones = Column(Text)
    
    # Auditoría
    fecha_evaluacion = Column(DateTime, default=get_utc_now)
    
    # Relaciones
    pedido = relationship("PedidoModel", back_populates="evaluacion")
    evaluador = relationship("EvaluadorModel", back_populates="evaluaciones")