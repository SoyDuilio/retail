# app/schemas/order_schemas.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Self
from datetime import datetime, date, time
from decimal import Decimal
import uuid

from .common_schemas import EstadoPedido, TipoVenta, TipoPago
from .user_schemas import Vendedor, Evaluador, Supervisor
from .client_schemas import Cliente
from .product_schemas import Producto

# =============================================
# ITEMS DE PEDIDO
# =============================================

class PedidoItemBase(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    ### CAMBIO 1: Eliminamos precio_unitario y descuento_aplicado. ###
    # El backend los calculará de forma segura basándose en las reglas de negocio.
    # El frontend ya no es responsable de enviar el precio.
    # precio_unitario: Decimal = Field(..., ge=0, decimal_places=2)
    # descuento_aplicado: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)

    @field_validator('cantidad')
    @classmethod
    def validate_cantidad(cls, v):
        if v <= 0:
            raise ValueError('Cantidad debe ser mayor que cero')
        return v

class PedidoItemCreate(PedidoItemBase):
    ### CAMBIO 2: Añadimos el campo para sobrescribir la tarifa de precio. ###
    # Si el vendedor quiere dar un precio especial (ej. de Mayorista) a este item,
    # el frontend enviará aquí el ID del "Tipo de Cliente" a usar para el cálculo.
    override_tipo_cliente_id: Optional[int] = None
    pass

class PedidoItemUpdate(BaseModel):
    cantidad: Optional[int] = Field(None, gt=0)
    # Mantenemos la opción de actualizar precios manualmente aquí,
    # ya que podría ser una acción permitida para un supervisor.
    precio_unitario: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    descuento_aplicado: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)

class PedidoItem(BaseModel): ### CAMBIO 3: Schema de lectura completo para el item ###
    id: int
    pedido_id: int
    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    descuento_aplicado: Optional[Decimal]
    subtotal: Decimal
    total: Decimal
    created_at: datetime
    producto: Optional[Producto] = None

    class Config:
        from_attributes = True

# =============================================
# PEDIDOS PRINCIPALES
# =============================================

class PedidoBase(BaseModel):
    # Ya no necesitamos vendedor_id aquí, lo obtendremos del token de autenticación.
    # vendedor_id: int
    cliente_id: int
    tipo_venta: TipoVenta
    tipo_pago: TipoPago = TipoPago.CREDITO
    latitud_pedido: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitud_pedido: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    observaciones: Optional[str] = None

class PedidoCreate(PedidoBase):
    items: List[PedidoItemCreate] = Field(..., min_items=1)

    @field_validator('items')
    @classmethod
    def validate_items_no_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('El pedido debe tener al menos un item')
        return v

class PedidoUpdate(BaseModel):
    tipo_pago: Optional[TipoPago] = None
    observaciones: Optional[str] = None
    items: Optional[List[PedidoItemUpdate]] = None

class Pedido(BaseModel): ### CAMBIO 4: Schema de lectura completo para el pedido ###
    id: int
    numero_pedido: str
    vendedor_id: int  # Añadido para mostrar quién creó el pedido
    cliente_id: int
    tipo_venta: TipoVenta
    tipo_pago: TipoPago
    latitud_pedido: Optional[Decimal]
    longitud_pedido: Optional[Decimal]
    observaciones: Optional[str]
    fecha: date
    hora: time
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime
    vendedor: Optional[Vendedor] = None
    cliente: Optional[Cliente] = None
    items: List[PedidoItem] = [] # Aseguramos que siempre sea una lista
    calificacion: Optional['Calificacion'] = None

    class Config:
        from_attributes = True

# =============================================
# CALIFICACIONES Y EVALUACIONES
# =============================================

class CalificacionBase(BaseModel):
    pedido_id: int
    evaluador_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    estado: EstadoPedido = EstadoPedido.PENDIENTE
    monto_solicitado: Decimal = Field(..., ge=0, decimal_places=2)
    monto_aprobado: Decimal = Field(default=0, ge=0, decimal_places=2)
    observaciones: Optional[str] = None

class CalificacionCreate(CalificacionBase):
    pass

class CalificacionUpdate(BaseModel):
    evaluador_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    estado: Optional[EstadoPedido] = None
    monto_aprobado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    observaciones: Optional[str] = None
    tiempo_evaluacion: Optional[int] = None  # Segundos que tomó evaluar

    @model_validator(mode='after')
    def validate_approval_logic(self) -> Self:
        # En lugar de 'values', ahora usamos 'self' para acceder a los campos
        estado = self.estado
        monto_aprobado = self.monto_aprobado
        
        if estado in [EstadoPedido.APROBADO, EstadoPedido.PARCIAL]:
            if not monto_aprobado or monto_aprobado <= 0:
                raise ValueError('Monto aprobado debe ser mayor que cero para pedidos aprobados o parciales')
        return self

class Calificacion(CalificacionBase):
    id: int
    fecha_evaluacion: Optional[datetime] = None
    tiempo_evaluacion: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    evaluador: Optional[Evaluador] = None
    supervisor: Optional[Supervisor] = None
    pedido: Optional[Pedido] = None

    class Config:
        from_attributes = True

# =============================================
# KDS (KITCHEN DISPLAY SYSTEM) PARA EVALUADORES
# =============================================

class KDSPedido(BaseModel):
    """Modelo para el Kitchen Display System de evaluadores"""
    pedido_id: int
    numero_pedido: str
    fecha: date
    hora: time
    vendedor_nombre: str
    vendedor_dni: str
    cliente_nombre: str
    cliente_ruc: str
    tipo_cliente: str
    total: Decimal
    tiempo_espera: int  # minutos desde creación
    prioridad: str = Field(default="media")  # alta, media, baja
    ubicacion: Optional[str] = None
    items_resumen: str  # Resumen de productos
    observaciones: Optional[str] = None
    tipo_venta: TipoVenta
    credito_disponible: Optional[Decimal] = None

    def calcular_prioridad(self) -> str:
        """Calcular prioridad basada en tiempo de espera y monto"""
        if self.tiempo_espera > 30:  # Más de 30 minutos
            return "alta"
        elif self.total > 1000:  # Pedidos grandes
            return "alta" 
        elif self.tiempo_espera > 15:
            return "media"
        return "baja"

class KDSFiltros(BaseModel):
    estado: Optional[EstadoPedido] = EstadoPedido.PENDIENTE
    prioridad: Optional[str] = None
    tipo_venta: Optional[TipoVenta] = None
    vendedor_id: Optional[int] = None
    tiempo_min: Optional[int] = None  # Filtrar por tiempo mínimo de espera

class KDSStats(BaseModel):
    total_pendientes: int
    promedio_tiempo_espera: int
    pedidos_alta_prioridad: int
    monto_total_pendiente: Decimal
    evaluador_activo: str

# =============================================
# PEDIDOS COMPLETOS (VISTAS)
# =============================================

class PedidoCompleto(BaseModel):
    """Vista completa del pedido con toda la información"""
    pedido_id: int
    numero_pedido: str
    fecha: date
    hora: time
    tipo_venta: TipoVenta
    tipo_pago: TipoPago
    vendedor_nombre: str
    vendedor_dni: str
    cliente_nombre: str
    cliente_ruc: str
    tipo_cliente: str
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    estado_evaluacion: Optional[EstadoPedido] = None
    monto_aprobado: Optional[Decimal] = None
    evaluador_nombre: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PedidoResumen(BaseModel):
    """Resumen de pedido para listas"""
    id: int
    numero_pedido: str
    fecha: date
    cliente_nombre: str
    total: Decimal
    estado: EstadoPedido
    tiempo_transcurrido: str  # "2h 15m"
    prioridad_color: str  # Color hex para UI

# =============================================
# FILTROS Y BÚSQUEDAS
# =============================================

class FiltrosPedidos(BaseModel):
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    vendedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    tipo_venta: Optional[TipoVenta] = None
    tipo_pago: Optional[TipoPago] = None
    estado: Optional[EstadoPedido] = None
    tipo_cliente_id: Optional[int] = None
    producto_id: Optional[int] = None
    monto_minimo: Optional[Decimal] = Field(None, ge=0)
    monto_maximo: Optional[Decimal] = Field(None, ge=0)
    numero_pedido: Optional[str] = None
    cliente_ruc: Optional[str] = None
    solo_credito: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class FiltrosCalificaciones(BaseModel):
    estado: Optional[EstadoPedido] = None
    evaluador_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    monto_min: Optional[Decimal] = Field(None, ge=0)
    monto_max: Optional[Decimal] = Field(None, ge=0)
    tiempo_evaluacion_max: Optional[int] = None  # Segundos
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

# =============================================
# REPORTES Y ESTADÍSTICAS
# =============================================

class ReportePedidos(BaseModel):
    periodo: str  # "2024-01", "2024-Q1", etc.
    total_pedidos: int
    pedidos_aprobados: int
    pedidos_rechazados: int
    pedidos_pendientes: int
    tasa_aprobacion: Decimal
    monto_total_solicitado: Decimal
    monto_total_aprobado: Decimal
    ticket_promedio: Decimal
    tiempo_promedio_evaluacion: int  # segundos

class RankingVendedorPedidos(BaseModel):
    posicion: int
    vendedor_id: int
    vendedor_nombre: str
    vendedor_dni: str
    total_pedidos: int
    total_ventas: Decimal
    promedio_pedido: Decimal
    pedidos_aprobados: int
    tasa_aprobacion: Decimal
    puntuacion: Decimal

class EstadisticasEvaluador(BaseModel):
    evaluador_id: int
    evaluador_nombre: str
    total_evaluaciones: int
    evaluaciones_aprobadas: int
    evaluaciones_rechazadas: int
    tasa_aprobacion: Decimal
    tiempo_promedio_evaluacion: int
    evaluaciones_hoy: int
    eficiencia_score: Decimal

class ReporteVentas(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    ventas_por_dia: List[dict]  # [{"fecha": "2024-01-01", "ventas": 1500.00}]
    ventas_por_tipo_cliente: List[dict]
    productos_mas_vendidos: List[dict]
    vendedores_top: List[RankingVendedorPedidos]
    resumen: ReportePedidos

# =============================================
# NOTIFICACIONES DE PEDIDOS
# =============================================

class NotificacionPedido(BaseModel):
    tipo: str  # pedido_nuevo, pedido_aprobado, pedido_rechazado
    pedido_id: int
    numero_pedido: str
    destinatario_id: int
    destinatario_tipo: str  # vendedor, evaluador, supervisor, cliente
    titulo: str
    mensaje: str
    datos_adicionales: Optional[dict] = None
    sonido: bool = True
    prioridad: str = Field(default="normal")  # normal, high, urgent

class RespuestaPedido(BaseModel):
    """Respuesta estándar para operaciones con pedidos"""
    success: bool
    pedido_id: Optional[int] = None
    numero_pedido: Optional[str] = None
    message: str
    data: Optional[dict] = None

# =============================================
# FLUJO DE EVALUACIÓN
# =============================================

class IniciarEvaluacion(BaseModel):
    pedido_id: int
    evaluador_id: int
    tiempo_inicio: datetime = Field(default_factory=datetime.now)

class FinalizarEvaluacion(BaseModel):
    pedido_id: int
    estado: EstadoPedido
    monto_aprobado: Decimal = Field(..., ge=0)
    observaciones: Optional[str] = None
    requiere_supervisor: bool = False

class EvaluacionRapida(BaseModel):
    """Para evaluaciones express de montos pequeños"""
    pedido_id: int
    aprobado: bool
    monto_aprobado: Optional[Decimal] = None
    observaciones: Optional[str] = None

class EscalarSupervisor(BaseModel):
    pedido_id: int
    motivo: str = Field(..., min_length=10)
    observaciones_evaluador: str
    supervisor_sugerido: Optional[int] = None

# =============================================
# CARRITO Y PEDIDO TEMPORAL
# =============================================

class ItemCarrito(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    precio_unitario: Optional[Decimal] = None  # Se calcula automáticamente
    notas: Optional[str] = None

class Carrito(BaseModel):
    cliente_id: int
    tipo_venta: TipoVenta
    items: List[ItemCarrito]
    observaciones: Optional[str] = None
    ubicacion_lat: Optional[Decimal] = None
    ubicacion_lng: Optional[Decimal] = None

class ResumenCarrito(BaseModel):
    items: List[dict]  # Items con precios calculados
    subtotal: Decimal
    descuentos_totales: Decimal
    total: Decimal
    credito_requerido: Decimal
    credito_disponible: Decimal
    puede_procesar: bool
    alertas: List[str]

# =============================================
# INTEGRACIÓN Y SINCRONIZACIÓN
# =============================================

class PedidoVFP(BaseModel):
    """Para sincronización con Visual FoxPro"""
    numero_pedido: str
    codigo_cliente_vfp: str
    fecha_pedido: date
    monto_total: Decimal
    estado_vfp: str
    sincronizado: bool = False
    fecha_sync: Optional[datetime] = None

class SincronizarPedido(BaseModel):
    pedido_id: int
    exportar_a_vfp: bool = True
    actualizar_stock: bool = True
    generar_factura: bool = False

class ResultadoSincronizacion(BaseModel):
    pedidos_procesados: int
    pedidos_exitosos: int
    pedidos_con_error: int
    errores: List[str]
    tiempo_procesamiento: int  # segundos

# =============================================
# VALIDACIONES Y REGLAS DE NEGOCIO
# =============================================

class ValidacionPedido(BaseModel):
    cliente_tiene_credito: bool
    productos_disponibles: bool
    montos_validos: bool
    ubicacion_valida: bool
    vendedor_activo: bool
    errores: List[str]
    advertencias: List[str]

class ReglaCredito(BaseModel):
    monto_maximo_sin_evaluacion: Decimal = Field(default=500)
    requiere_supervisor_monto: Decimal = Field(default=5000)
    dias_vencimiento_credito: int = Field(default=30)
    tasa_interes_mora: Decimal = Field(default=2.5)

class ConfiguracionPedidos(BaseModel):
    auto_aprobar_monto_menor: Decimal = Field(default=200)
    requiere_ubicacion: bool = True
    permite_pedido_sin_stock: bool = False
    descuento_maximo_vendedor: Decimal = Field(default=10)
    tiempo_max_evaluacion_minutos: int = Field(default=30)

# =============================================
# AUDITORIA Y TRAZABILIDAD
# =============================================

class AuditoriaPedido(BaseModel):
    pedido_id: int
    accion: str  # creado, modificado, evaluado, aprobado, rechazado, cancelado
    usuario_id: int
    usuario_tipo: str
    valores_anteriores: Optional[dict] = None
    valores_nuevos: Optional[dict] = None
    observaciones: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None

class TrazabilidadPedido(BaseModel):
    pedido_id: int
    historial: List[AuditoriaPedido]
    estado_actual: EstadoPedido
    tiempo_total_proceso: Optional[int] = None  # minutos desde creación hasta resolución

# Forward reference resolution
Pedido.model_rebuild()
Calificacion.model_rebuild() # Es buena práctica añadirlo si hay referencias cruzadas