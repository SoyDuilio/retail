# models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import uuid

# =============================================
# ENUMS
# =============================================

class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    PARCIAL = "parcial"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

class TipoVenta(str, Enum):
    EXTERNA = "externa"
    INTERNA = "interna"

class TipoPago(str, Enum):
    CREDITO = "credito"
    CONTADO = "contado"
    YAPE = "yape"
    PLIN = "plin"

class TipoMensaje(str, Enum):
    PEDIDO_NUEVO = "pedido_nuevo"
    PEDIDO_APROBADO = "pedido_aprobado"
    PEDIDO_RECHAZADO = "pedido_rechazado"
    MENSAJE_GENERAL = "mensaje_general"
    CHAT_VOZ = "chat_voz"

class RolUsuario(str, Enum):
    VENDEDOR = "vendedor"
    EVALUADOR = "evaluador"
    SUPERVISOR = "supervisor"
    CLIENTE = "cliente"

# =============================================
# MODELOS BASE
# =============================================

class TipoClienteBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    descripcion: Optional[str] = None
    activo: bool = True

class TipoClienteCreate(TipoClienteBase):
    pass

class TipoCliente(TipoClienteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoriaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    activo: bool = True

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UnidadMedidaBase(BaseModel):
    nombre: str = Field(..., max_length=20)
    abreviatura: str = Field(..., max_length=5)
    activo: bool = True

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedida(UnidadMedidaBase):
    id: int

    class Config:
        from_attributes = True

# =============================================
# USUARIOS
# =============================================

class VendedorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class VendedorCreate(VendedorBase):
    pass

class Vendedor(VendedorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EvaluadorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class EvaluadorCreate(EvaluadorBase):
    pass

class Evaluador(EvaluadorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupervisorBase(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    nombres: str = Field(..., max_length=100)
    apellidos: str = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=100)
    activo: bool = True

    @validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v

class SupervisorCreate(SupervisorBase):
    pass

class Supervisor(SupervisorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# =============================================
# PRODUCTOS
# =============================================

class ProductoBase(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    categoria_id: int
    unidad_medida_id: int
    precio_base: Decimal = Field(..., ge=0, decimal_places=2)
    stock_actual: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=0, ge=0)
    activo: bool = True

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    categoria: Optional[Categoria] = None
    unidad_medida: Optional[UnidadMedida] = None

    class Config:
        from_attributes = True

class PrecioClienteBase(BaseModel):
    producto_id: int
    tipo_cliente_id: int
    precio: Decimal = Field(..., ge=0, decimal_places=2)
    descuento_volumen_1: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_1: Optional[int] = Field(default=10, ge=1)
    descuento_volumen_2: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_2: Optional[int] = Field(default=50, ge=1)
    descuento_volumen_3: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)
    cantidad_minima_3: Optional[int] = Field(default=100, ge=1)
    activo: bool = True

class PrecioClienteCreate(PrecioClienteBase):
    pass

class PrecioCliente(PrecioClienteBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =============================================
# CLIENTES
# =============================================

class ClienteBase(BaseModel):
    ruc: str = Field(..., min_length=11, max_length=11)
    razon_social: Optional[str] = Field(None, max_length=200)
    nombres: Optional[str] = Field(None, max_length=100)
    apellidos: Optional[str] = Field(None, max_length=100)
    direccion: str
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    tipo_cliente_id: int
    contacto_nombres: Optional[str] = Field(None, max_length=100)
    whatsapp: Optional[str] = Field(None, max_length=15)
    limite_credito: Decimal = Field(default=0, ge=0, decimal_places=2)
    credito_usado: Decimal = Field(default=0, ge=0, decimal_places=2)
    activo: bool = True

    @validator('ruc')
    def validate_ruc(cls, v):
        if not v.isdigit():
            raise ValueError('RUC debe contener solo números')
        return v

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tipo_cliente: Optional[TipoCliente] = None
    credito_disponible: Optional[Decimal] = None

    class Config:
        from_attributes = True

# =============================================
# PEDIDOS
# =============================================

class PedidoItemBase(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0, decimal_places=2)
    descuento_aplicado: Optional[Decimal] = Field(default=0, ge=0, le=100, decimal_places=2)

class PedidoItemCreate(PedidoItemBase):
    pass

class PedidoItem(PedidoItemBase):
    id: int
    pedido_id: uuid.UUID
    subtotal: Decimal
    total: Decimal
    created_at: datetime
    producto: Optional[Producto] = None

    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    vendedor_id: int
    cliente_id: int
    tipo_venta: TipoVenta
    tipo_pago: TipoPago = TipoPago.CREDITO
    latitud_pedido: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    longitud_pedido: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)
    observaciones: Optional[str] = None

class PedidoCreate(PedidoBase):
    items: List[PedidoItemCreate] = Field(..., min_items=1)

class Pedido(PedidoBase):
    id: uuid.UUID
    numero_pedido: str
    fecha: date
    hora: time
    subtotal: Decimal
    descuento_total: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime
    vendedor: Optional[Vendedor] = None
    cliente: Optional[Cliente] = None
    items: Optional[List[PedidoItem]] = None
    calificacion: Optional['Calificacion'] = None

    class Config:
        from_attributes = True

# =============================================
# CALIFICACIONES
# =============================================

class CalificacionBase(BaseModel):
    pedido_id: uuid.UUID
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
# MENSAJERÍA Y NOTIFICACIONES
# =============================================

class MensajeBase(BaseModel):
    remitente_id: int
    remitente_tipo: RolUsuario
    destinatario_id: Optional[int] = None
    destinatario_tipo: Optional[RolUsuario] = None
    tipo_mensaje: TipoMensaje
    titulo: str = Field(..., max_length=200)
    contenido: str
    pedido_id: Optional[uuid.UUID] = None

class MensajeCreate(MensajeBase):
    pass

class Mensaje(MensajeBase):
    id: int
    leido: bool = False
    enviado: bool = False
    fecha_envio: datetime
    fecha_lectura: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificacionPush(BaseModel):
    usuario_id: int
    usuario_tipo: RolUsuario
    titulo: str
    mensaje: str
    data: Optional[dict] = None
    sonido: bool = True

# =============================================
# CHAT DE VOZ
# =============================================

class ConversacionVozBase(BaseModel):
    pedido_id: Optional[uuid.UUID] = None
    vendedor_id: int
    cliente_id: int
    metodo_transcripcion: str = Field(default="web_speech_api")

class ConversacionVozCreate(ConversacionVozBase):
    pass

class ConversacionVoz(ConversacionVozBase):
    id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    duracion_segundos: Optional[int] = None

    class Config:
        from_attributes = True

class TranscripcionBase(BaseModel):
    conversacion_id: int
    hablante: str = Field(..., regex="^(vendedor|cliente)$")
    texto_original: str
    texto_procesado: Optional[str] = None
    confianza: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=2)
    timestamp_audio: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

class TranscripcionCreate(TranscripcionBase):
    pass

class Transcripcion(TranscripcionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =============================================
# SESIONES Y AUTENTICACIÓN
# =============================================

class LoginRequest(BaseModel):
    usuario: str  # DNI para trabajadores, RUC para clientes
    clave: str    # DNI para trabajadores, RUC para clientes
    tipo_usuario: RolUsuario
    ubicacion_lat: Optional[Decimal] = Field(None, ge=-90, le=90, decimal_places=8)
    ubicacion_lng: Optional[Decimal] = Field(None, ge=-180, le=180, decimal_places=8)

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_tipo: Optional[RolUsuario] = None
    nombre_completo: Optional[str] = None
    redirect_url: Optional[str] = None
    mensaje: Optional[str] = None

class SesionActiva(BaseModel):
    id: int
    usuario_id: int
    usuario_tipo: RolUsuario
    token_session: uuid.UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    ubicacion_lat: Optional[Decimal] = None
    ubicacion_lng: Optional[Decimal] = None
    ultimo_ping: datetime
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

# =============================================
# DASHBOARD Y REPORTES
# =============================================

class DashboardMetricas(BaseModel):
    pedidos_hoy: int
    pedidos_ayer: int
    ventas_hoy: Optional[Decimal]
    ventas_ayer: Optional[Decimal]
    evaluaciones_pendientes: int
    aprobaciones_hoy: int
    rechazos_hoy: int
    vendedores_activos_hoy: int
    productos_stock_bajo: int

class PedidoCompleto(BaseModel):
    pedido_id: uuid.UUID
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
    estado_evaluacion: Optional[EstadoPedido]
    monto_aprobado: Optional[Decimal]
    evaluador_nombre: Optional[str]
    observaciones: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ProductoPrecio(BaseModel):
    producto_id: int
    codigo: str
    producto_nombre: str
    descripcion: Optional[str]
    categoria: str
    unidad_medida: str
    unidad_abrev: str
    tipo_cliente_id: int
    tipo_cliente: str
    precio: Decimal
    descuento_volumen_1: Optional[Decimal]
    cantidad_minima_1: Optional[int]
    descuento_volumen_2: Optional[Decimal]
    cantidad_minima_2: Optional[int]
    descuento_volumen_3: Optional[Decimal]
    cantidad_minima_3: Optional[int]
    stock_actual: int
    stock_minimo: int
    estado_stock: str

    class Config:
        from_attributes = True

# =============================================
# FILTROS Y BÚSQUEDAS
# =============================================

class FiltrosPedidos(BaseModel):
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    vendedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    tipo_venta: Optional[TipoVenta] = None
    estado: Optional[EstadoPedido] = None
    tipo_cliente_id: Optional[int] = None
    producto_id: Optional[int] = None
    monto_minimo: Optional[Decimal] = None
    monto_maximo: Optional[Decimal] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class FiltrosProductos(BaseModel):
    categoria_id: Optional[int] = None
    tipo_cliente_id: Optional[int] = None
    buscar: Optional[str] = None
    stock_bajo: Optional[bool] = None
    activo: Optional[bool] = True
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)

class RankingVendedor(BaseModel):
    vendedor_id: int
    vendedor_nombre: str
    vendedor_dni: str
    total_pedidos: int
    total_ventas: Decimal
    promedio_pedido: Decimal
    pedidos_aprobados: int
    tasa_aprobacion: Decimal

# =============================================
# RESPUESTAS API
# =============================================

class Response(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    success: bool
    data: List[dict]
    total: int
    page: int
    size: int
    pages: int
    message: Optional[str] = None

# =============================================
# VALIDACIONES ESPECIALES
# =============================================

class CalculoPrecio(BaseModel):
    producto_id: int
    tipo_cliente_id: int
    cantidad: int

class ResultadoPrecio(BaseModel):
    precio_unitario: Decimal
    descuento_aplicado: Decimal
    precio_final: Decimal
    subtotal: Decimal
    total: Decimal
    descuento_por_volumen: bool
    nivel_descuento: Optional[int] = None

class ValidacionCredito(BaseModel):
    cliente_id: int
    monto_solicitado: Decimal

class ResultadoCredito(BaseModel):
    cliente_id: int
    limite_credito: Decimal
    credito_usado: Decimal
    credito_disponible: Decimal
    monto_solicitado: Decimal
    puede_aprobar: bool
    monto_maximo_aprobable: Decimal
    observaciones: Optional[str] = None

# =============================================
# WEBSOCKETS
# =============================================

class WebSocketMessage(BaseModel):
    type: str  # "pedido_nuevo", "pedido_aprobado", "mensaje", "ping"
    data: dict
    timestamp: datetime = Field(default_factory=datetime.now)
    sender_id: Optional[int] = None
    sender_type: Optional[RolUsuario] = None

class KDSPedido(BaseModel):
    """Modelo para el Kitchen Display System de evaluadores"""
    pedido_id: uuid.UUID
    numero_pedido: str
    fecha: date
    hora: time
    vendedor_nombre: str
    cliente_nombre: str
    tipo_cliente: str
    total: Decimal
    tiempo_espera: int  # minutos desde creación
    prioridad: str  # "alta", "media", "baja"
    ubicacion: Optional[str] = None
    items_resumen: str  # Resumen de productos
    observaciones: Optional[str] = None

# Forward reference resolution
Pedido.model_rebuild()